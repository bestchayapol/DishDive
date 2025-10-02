import os
import json
import re
import threading
import time
import logging
from openai import OpenAI
import threading
import time
from .utils import INGREDIENT_ROOTS  # reuse single source of truth for ingredients

PROMPT_TEMPLATE = """
You are an extraction engine for Thai restaurant reviews.

TASK: Return an array (raw JSON only) of dish objects for this single review.

Restaurant: {restaurant}
Review: "{review}"

RULES (concise):
1. Split multiple dishes joined by และ, กับ, และก็, หรือ, ,
2. Use most specific phrase.
3. Keep dish if mentioned even without sentiment (empty lists allowed).
4. Sentiment lists: taste / texture / doneness / temperature / presentation only.
5. A valid dish must include an ingredient/prep root from this set OR be a known multi-word dish (e.g., ปลาหมึกนึ่งมะนาว, ข้าวผัดกุ้ง, กุ้งเผา, ยำวุ้นเส้นรวมมิตร, กุ้งซอสมะขาม).
6. DO NOT output generic placeholders like เมนูรวม/อาหาร/เมนู or quality/ambience/price words alone (e.g., อร่อย, บรรยากาศดี, ราคาไม่แพง, คุ้มค่า, สะอาด, สด, เด็ด, แซ่บ) unless attached to a valid dish root.
7. If no valid dish is present, return [] exactly.
8. Ignore phrases starting with อาหาร / เมนู lacking a valid root.
9. Copy restaurant name exactly in every object.
10. cuisine: choose from [thai,chinese,japanese,korean,italian,american,vietnamese,indian,mexican,fusion,others].
11. restriction: one of ["halal","vegan","buddhist vegan", null].

Schema:
[
  {
    "restaurant": "…",
    "dish": "…",
    "cuisine": "…",
    "restriction": null,
    "sentiment": {"positive":[],"negative":[]}
  }
]

Return ONLY the JSON array.
"""

## NOTE: Secondary LLM fallback removed to save tokens. Only primary + rule-based heuristic now.

_client = None
_last_call_ts = 0.0
_call_lock = threading.Lock()
# Limit concurrent OpenAI calls across threads (helps avoid 429s)
_max_concurrent = max(1, int(os.getenv("OPENAI_MAX_CONCURRENT", "2")))
_call_sema = threading.Semaphore(_max_concurrent)
_logger = logging.getLogger(__name__)

# --- Lightweight metrics to reconcile dashboard vs actual attempts ---
_metrics = {
    "attempts": 0,
    "successes": 0,
    "rate_limits": 0,
    "other_errors": 0,
}
_metrics_lock = threading.Lock()

# Optional global request budget cap for cost control
_request_cap = int(os.getenv("OPENAI_REQUEST_CAP", "0") or 0)
_request_count = 0
_request_lock = threading.Lock()

def get_llm_metrics(reset: bool = False):
    """Return a snapshot of LLM call metrics. Optionally reset counters."""
    with _metrics_lock:
        snap = dict(_metrics)
        if reset:
            for k in _metrics:
                _metrics[k] = 0
        return snap

def _get_client():
    global _client
    if _client is None:
        _client = OpenAI()  # Uses OPENAI_API_KEY from environment
    return _client

FORBIDDEN_DISHES = {"เมนูรวม","เมนูต่างๆ","อาหารรวม","assorted","อาหาร","เมนู"}

# Broad regex to detect presence of potential dish tokens (roots & common dishes)
DISH_REGEX = re.compile(
    r"(ต้มยำ|ลาบ|ส้มตำ|ก้อย|ผัด|แกง|เกี๊ยวซ่า|เกี๊ยว|เต้าหู้|ปลาหมึก|ปลากระพง|คอหมูย่าง|หมูย่าง|ไก่ทอด|ปีกไก่|กระดูกหมู|ผัดไทย|กะเพรา|กะเพร|ข้าวผัด|ปลาเผา|ยำ)"
)

def _safe_parse(raw: str):
    if not raw:
        return None
    raw = raw.strip()
    # Attempt to isolate JSON array
    if '[' in raw and ']' in raw:
        start = raw.find('[')
        end = raw.rfind(']') + 1
        snippet = raw[start:end]
    else:
        snippet = raw
    try:
        return json.loads(snippet)
    except Exception:
        return None

def _needs_fallback(parsed, review: str) -> bool:
    if parsed is None:
        return True
    if not isinstance(parsed, list):
        return True
    if len(parsed) == 0 and DISH_REGEX.search(review):
        return True
    # If all dishes are forbidden generics
    dishes = [str(item.get('dish','')).strip() for item in parsed if isinstance(item, dict)]
    if dishes and all(d in FORBIDDEN_DISHES for d in dishes):
        return True
    return False

# -------- Rule-based final fallback (token-free) ---------
_RB_METHODS = ["ทอด","ผัด","ย่าง","นึ่ง","ต้ม","แกง","เผา","อบ"]
_RB_FLAVOR_PARTS = ["มะนาว","กระเทียม","พริก","ปลาร้า","สมุนไพร"]
_RB_POSITIVE = ["อร่อย","แซ่บ","เด็ด","ดี","หอม","กรอบ","เข้มข้น","สด","นุ่ม","หวาน","กลมกล่อม"]
_RB_NEGATIVE = ["เค็ม","จืด","เหนียว","มันไป","หวานไป","เผ็ดไป","ไม่อร่อย","คาว"]

_THAI_LETTERS = r"ก-๙"

def _rule_based_extract(restaurant: str, review: str):
    dishes = []
    lowered = review  # Thai not case-sensitive
    sentiments_pos = set()
    sentiments_neg = set()
    # Pre-token sentiment capture (simple presence scan)
    for tok in _RB_POSITIVE:
        if tok in lowered:
            sentiments_pos.add(tok)
    for tok in _RB_NEGATIVE:
        if tok in lowered:
            sentiments_neg.add(tok)

    # Build regex patterns for ingredients with optional method/flavor right after them (no space or with a single space)
    # e.g. ปลาหมึกนึ่งมะนาว / ปลาหมึก นึ่ง มะนาว
    candidates = set()
    for ing in INGREDIENT_ROOTS:
        for match in re.finditer(re.escape(ing), review):
            start = match.start()
            tail = review[match.end(): match.end()+24]  # look ahead limited span
            # Collect following method/flavor tokens contiguous or separated by single spaces
            extra_tokens = []
            # Split on spaces to examine first few tokens
            parts = re.split(r"\s+", tail.strip())
            for p in parts[:3]:
                p_clean = p.strip().strip('.,!?:;"')
                if not p_clean:
                    continue
                if any(p_clean.startswith(x) for x in _RB_METHODS + _RB_FLAVOR_PARTS):
                    extra_tokens.append(p_clean)
                else:
                    # stop if token not a method/flavor
                    break
            phrase = ing + ("" if not extra_tokens else ("".join(extra_tokens)))
            # Trim trailing sentiment tokens if appended without space
            for s in _RB_POSITIVE + _RB_NEGATIVE:
                if phrase.endswith(s):
                    phrase = phrase[: -len(s)]
            phrase = phrase.strip()
            if phrase and phrase not in FORBIDDEN_DISHES:
                candidates.add(phrase)

    # Fallback: if no combined phrases, allow bare ingredients present
    if not candidates:
        for ing in INGREDIENT_ROOTS:
            if ing in review and ing not in FORBIDDEN_DISHES:
                candidates.add(ing)

    results = []
    for c in sorted(candidates, key=len):
        # sentiment window: take up to 30 chars after occurrence
        pos_list = []
        neg_list = []
        for m in re.finditer(re.escape(c), review):
            window = review[m.end(): m.end()+40]
            for tok in _RB_POSITIVE:
                if tok in window and tok not in pos_list:
                    pos_list.append(tok)
            for tok in _RB_NEGATIVE:
                if tok in window and tok not in neg_list:
                    neg_list.append(tok)
        results.append({
            "restaurant": restaurant,
            "dish": c,
            "cuisine": "thai",  # heuristic default
            "restriction": None,
            "sentiment": {"positive": pos_list, "negative": neg_list}
        })
    return results

def gpt35_extract(restaurant, review):
    try:
        client = _get_client()
        # Sanity check API key present
        assert os.getenv('OPENAI_API_KEY'), 'OPENAI_API_KEY not set in environment for this process'
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Hard kill-switch: if set, skip OpenAI calls entirely
        if os.getenv("OPENAI_DISABLED", "").lower() in ("1", "true", "yes"): 
            _logger.info("OPENAI_DISABLED set; using rule-based extractor only")
            rb = _rule_based_extract(restaurant, review)
            if rb:
                return json.dumps(rb, ensure_ascii=False), "disabled-rule-based"
            return "[]", "disabled-rule-based-empty"

        # Budget cap: if a request cap is set and reached, skip further LLM calls
        global _request_count
        if _request_cap > 0:
            with _request_lock:
                if _request_count >= _request_cap:
                    rb = _rule_based_extract(restaurant, review)
                    if rb:
                        return json.dumps(rb, ensure_ascii=False), "budget-rule-based"
                    return "[]", "budget-rule-based-empty"

        # If caller provided a hint dish (from submit flow), lightly include it to aid extraction
        hint_dish = os.getenv("HINT_DISH_NAME", "").strip()
        hinted_review = review
        if hint_dish:
            hinted_review = f"(dish mentioned: {hint_dish}) " + review

        # Avoid Python str.format on template with many JSON braces causing KeyError.
        def _fill(template: str) -> str:
            return template.replace('{restaurant}', restaurant).replace('{review}', hinted_review)

        primary_prompt = _fill(PROMPT_TEMPLATE)
        # Global lightweight rate limit across threads + bounded concurrency
        min_interval = float(os.getenv("OPENAI_MIN_INTERVAL_SEC", "0.5"))
        global _last_call_ts
        primary_resp = None
        attempts = max(1, int(os.getenv("OPENAI_RETRY_ATTEMPTS", "3")))
        backoff = float(os.getenv("OPENAI_RETRY_BACKOFF", "1.5"))
        delay = float(os.getenv("OPENAI_RETRY_INITIAL_DELAY", "1.0"))
        last_err = None
        for i in range(attempts):
            with _call_sema:
                with _call_lock:
                    now = time.time()
                    wait = _last_call_ts + min_interval - now
                    if wait > 0:
                        time.sleep(wait)
                    _last_call_ts = time.time()
                try:
                    # Metrics: attempt
                    with _metrics_lock:
                        _metrics["attempts"] += 1
                    _logger.debug(
                        "openai attempt #%d ts=%.3f model=%s",
                        _metrics["attempts"], time.time(), model,
                    )
                    primary_resp = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": primary_prompt}],
                        temperature=0.0,
                        max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "320")),
                        user=os.getenv("OPENAI_USER_TAG", f"DishDive/{os.getenv('COMPUTERNAME','unknown')}")
                    )
                    # Increment request count after a real call
                    if _request_cap > 0:
                        with _request_lock:
                            _request_count += 1
                    # Metrics: success
                    with _metrics_lock:
                        _metrics["successes"] += 1
                    break
                except Exception as e:
                    last_err = e
                    # For rate limit or transient errors, sleep and retry; else break.
                    msg = str(e)
                    is_rate = "429" in msg or "RateLimit" in msg
                    is_transient = any(x in msg for x in ["timeout","Timeout","Temporary","temporarily","Connection reset","Service Unavailable","502","503","504"])
                    with _metrics_lock:
                        if is_rate:
                            _metrics["rate_limits"] += 1
                        else:
                            _metrics["other_errors"] += 1
                    if i < attempts - 1 and (is_rate or is_transient):
                        _logger.warning("openai call failed (attempt %s/%s): %s; retrying in %.1fs", i+1, attempts, type(e).__name__, delay)
                        time.sleep(delay)
                        delay *= backoff
                        continue
                    # No more retries or non-retryable error
                    break
        if primary_resp is None:
            return json.dumps([{ "restaurant": restaurant, "dish": "", "cuisine": "", "restriction": None, "sentiment": {"positive": [], "negative": []}, "_error": f"primary_call_failed:{type(last_err).__name__ if last_err else 'Unknown'}:{str(last_err)[:160] if last_err else ''}" }], ensure_ascii=False), "error-primary"
        primary_text = primary_resp.choices[0].message.content.strip()
        # Best-effort token usage logging
        try:
            u = getattr(primary_resp, "usage", None)
            if u:
                _logger.debug(
                    "openai usage model=%s prompt=%s completion=%s total=%s",
                    model, getattr(u, "prompt_tokens", None), getattr(u, "completion_tokens", None), getattr(u, "total_tokens", None)
                )
        except Exception:
            # Usage extraction is best-effort only
            pass
        parsed = _safe_parse(primary_text)

        if _needs_fallback(parsed, review):
            # Directly use rule-based heuristic (no extra LLM call)
            rb = _rule_based_extract(restaurant, review)
            if rb:
                return json.dumps(rb, ensure_ascii=False), "rule-based"
            # If primary only contained generic placeholders, do NOT keep them.
            # Return an empty array to avoid polluting data with "เมนูรวม" etc.
            return "[]", "rule-based-empty"
        return primary_text, "primary"
    except Exception as e:
        # Catch-all for any unforeseen errors (parsing logic etc.)
        return json.dumps([{ "restaurant": restaurant, "dish": "", "cuisine": "", "restriction": None, "sentiment": {"positive": [], "negative": []}, "_error": f"unhandled_exception:{type(e).__name__}:{str(e)[:160]}" }], ensure_ascii=False), "exception"