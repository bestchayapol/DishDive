import pandas as pd
import json
import os
import re
import ast
import time
import logging
from contextlib import contextmanager
import psycopg2
import psycopg2.extras as pg_extras
from psycopg2 import pool as pg_pool
from psycopg2 import sql as pg_sql
from psycopg2 import Error
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
# from database_config import DATABASE_CONFIG  # retained for other scripts; not used here

# from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain.globals import set_debug, get_debug

# Set debug mode for LangChain
set_debug(False)      # Set to True for debugging, False for production                                                                                                                

# ---------------------------
# Logging Setup
# ---------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
LOGGER = logging.getLogger("dishdive.scraper")

# PostgreSQL target (KMUTT)
PG_CONFIG = {
    'host': 'dishdive.sit.kmutt.ac.th',
    'port': 5432,
    'user': 'root',
    'password': 'tungtungtungtungsahur',
    'database': 'postgres',
}
   
# Run-level base to continue rev_ext_id without collisions across batches
REV_EXT_BASE: int | None = None
_PG_AVAILABLE: bool | None = None
_PG_LAST_CHECK_TS: float | None = None
_PG_POOL: pg_pool.SimpleConnectionPool | None = None
   
def load_csv(filepath: str, max_rows: int = 150000) -> pd.DataFrame:
    
    df = pd.read_csv(filepath)
    return df.head(max_rows)[["restaurant_name", "review_text"]]

prompt = PromptTemplate.from_template(
"""
You are a food review analysis expert specialized in Thai cuisine. Your task is to analyze a Thai restaurant review and extract structured insights for each dish mentioned.

Restaurant Name: {restaurant}

Review:
“{review}”

Please extract and return the following information for each food dish found in the review:

1. Dish Name: Clearly identify the name of the dish being reviewed (e.g., "ต้มยำกุ้ง", "ข้าวผัด", "คอหมูย่าง"). There can be more than one dish per review.
2. Cuisine: Identify the closest matching cuisine for a dish (ต้มยำกุ้ง is "thai", pizza is "italian"). Check the dish name first; if that's ambiguous (e.g., steak), use the restaurant name as a hint. If still unclear, set to "Others". Only one cuisine per dish; use "Fusion" for fusion dishes.
3. Restrictions: Identify potential restrictions of a dish ("halal", "vegan", "thai buddhist vegan"). If none are detected, set to null. Consider both the dish name and the restaurant name, but do not assume restrictions that contradict the dish.
4. Sentiment (STRICT, VERBATIM):
     - Extract only attribute-specific keywords about the dish (taste, texture, temperature, presentation, special characteristics).
     - Positive/negative lists must contain ONLY exact words or phrases that appear in the review text, verbatim (no synonyms, no paraphrases, no inferred intensifiers).
     - Do NOT upgrade/soften intensity (e.g., if the review says "อร่อย" do NOT output "อร่อยมาก" unless the word "มาก" actually appears).
     - If a keyword does not refer to a dish (e.g., general service/price/ambience like "บริการดี", "ราคาไม่แพง"), ignore it for sentiment.
     - If no dish-specific sentiment is present, use an empty list.

General rules:
- If no explicit dish/menu item name is found in the review, return an empty JSON array [] (no text, just []).
- If the review mentions only generic words like "อาหาร", "เมนู", "ฟู้ด", or ratings like "food: 4" without naming a specific dish/menu item, return an empty JSON array [] (no text, just []).
- Dish must be a non-empty string. Never output null, empty string, or placeholders (e.g., "-", "N/A"). If you cannot identify a specific dish name, return nothing (no output).
- Return raw JSON only; do not include explanations or comments.

Output Format (JSON array):
[
    {{
        "review_id":  <Review ID>,
        "restaurant": <Restaurant Name>,
        "dish": <Dish Name>,
        "cuisine":  <Cuisine Type>,
        "restriction":  <Restriction Type>,
        "sentiment": {{
            "positive":  ["..."],
            "negative":  ["..."]
        }}
    }}
]

Examples (for calibration; these are not the current input):
1) Input: "พนักงานบริการดี อาหารอร่อย ราคาไม่แพง บริการ รับประทานที่ร้าน"
    Output:  []

2) Input: "ต้มยำกุ้ง อร่อย ราคาไม่แพง"
     Output: [{{
         "review_id": 1,
         "restaurant": "<ignored>",
         "dish": "ต้มยำกุ้ง",
         "cuisine": "thai",
         "restriction": null,
         "sentiment": {{ "positive": ["อร่อย"], "negative": [] }}
     }}]

3) Input: "ส้มตำข้าวโพดหวานไปนิด"
     Output: [{{
         "review_id": 2,
         "restaurant": "<ignored>",
         "dish": "ส้มตำข้าวโพด",
         "cuisine": "thai",
         "restriction": null,
         "sentiment": {{ "positive": [], "negative": ["หวานไปนิด"] }}
     }}]

4) Input: "สาเกร้อนคือดีมากแต่แพงไป"
     Output: [{{
         "review_id": 3,
         "restaurant": "<ignored>",
         "dish": "สาเกร้อน",
         "cuisine": "japanese",
         "restriction": null,
         "sentiment": {{ "positive": ["ดีมาก"], "negative": ["แพงไป"] }}
     }}]

5) Input: "ให้คะแนน food: 4 แต่ไม่ได้สั่งเมนูอะไรพิเศษ"
    Output:  []

Anti-example (do NOT do this):
Input: "ไม่ได้พูดถึงชื่อเมนูเฉพาะ อาหารโอเค"
Wrong Output: [{{"dish": null, "sentiment": {{"positive": ["โอเค"], "negative": []}}}}]
Correct Output:  []

Do not include any explanation, reasoning, Markdown, or comments — only return raw JSON that closes all brackets/braces (or return nothing when instructed).
"""
)

def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default

def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except Exception:
        return default

def _bool_env(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}

def _log_config_summary():
    try:
        LOGGER.info(
            "Config: PG host=%s db=%s sslmode=%s | LLM model=%s base_url=%s | Threads=%s",
            PG_CONFIG.get('host'),
            PG_CONFIG.get('database'),
            os.environ.get("PG_SSLMODE", "disable"),
            os.environ.get("OLLAMA_MODEL", "qwen3:1.7b"),
            os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            _int_env("OLLAMA_THREADS", 2),
        )
    except Exception:
        pass

def build_ollama_llm() -> OllamaLLM:
    # Tune for lower CPU usage by default; override via env
    num_ctx = _int_env("OLLAMA_NUM_CTX", 768)
    num_predict = _int_env("OLLAMA_NUM_PREDICT", 128)
    temperature = _float_env("OLLAMA_TEMPERATURE", 0.2)
    top_p = _float_env("OLLAMA_TOP_P", 0.9)
    repeat_penalty = _float_env("OLLAMA_REPEAT_PENALTY", 1.05)
    num_thread = _int_env("OLLAMA_THREADS", 2)
    json_mode = _bool_env("OLLAMA_JSON_MODE", True)

    # Many Ollama backends accept these as top-level kwargs; fallback-safe if ignored
    return OllamaLLM(
        model=os.environ.get("OLLAMA_MODEL", "qwen3:1.7b"),
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        num_ctx=num_ctx,
        num_predict=num_predict,
        temperature=temperature,
        top_p=top_p,
        repeat_penalty=repeat_penalty,
        num_thread=num_thread,
        # Enforce valid JSON output when enabled (Ollama JSON mode)
        **({"format": "json"} if json_mode else {}),
    )

llm = build_ollama_llm()
chain = prompt | llm

# CSV sourcing will be done inside main() to avoid side effects on import

def clean_model_output(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def is_balanced_json(s):
    stack = []
    pairs = {'{': '}', '[': ']'}
    for c in s:
        if c in pairs:
            stack.append(pairs[c])
        elif c in pairs.values():
            if not stack or c != stack.pop():
                return False
    return not stack

def has_unterminated_string(json_str):
    count = 0
    escaped = False
    for c in json_str:
        if c == '\\' and not escaped:
            escaped = True
        elif c == '"' and not escaped:
            count += 1
        else:
            escaped = False
    return count % 2 != 0

def extract_json(text: str) -> str:
    cleaned = clean_model_output(text).strip()
    # Fast path: if the whole response is valid JSON, return it directly
    if cleaned:
        try:
            json.loads(cleaned)
            return cleaned
        except Exception:
            pass
    # Try to find a JSON array (including empty [])
    match_array = re.search(r'\[\s*(?:\{.*?\}\s*(?:,\s*\{.*?\}\s*)*)?\]', cleaned, re.DOTALL)
    if match_array:
        return match_array.group(0)
    # Try to find a JSON object
    match_obj = re.search(r'\{.*?\}', cleaned, re.DOTALL)
    if match_obj:
        return match_obj.group(0)
    return ""

_GENERIC_KWS = set([
    "บริการ", "พนักงาน", "ราคา", "บรรยากาศ", "สะอาด", "คิว", "ที่จอด", "เพลง", "รอ", "รวดเร็ว",
    "service", "staff", "price", "ambience", "parking", "clean", "queue",
])
_DISH_CUES = set([
    "ต้ม", "ผัด", "ทอด", "แกง", "ยำ", "ตำ", "ก๋วยเตี๋ยว", "ข้าว", "ซุป", "ซูชิ", "ราเมง",
    "พิซซ่า", "สเต๊ก", "ส้มตำ", "ต้มยำ", "ไก่", "หมู", "กุ้ง", "ปลา", "พาสต้า", "เบอร์เกอร์",
    "pizza", "sushi", "ramen", "steak", "tom yum", "noodle", "fried", "soup", "pasta", "burger",
])

def should_skip_review(review: str, restaurant: str | None = None) -> bool:
    """Heuristic prefilter to avoid LLM calls when no dish-like signals are present.
    Skips when review is short or only generic service/price/ambience mentions.
    """
    if not isinstance(review, str):
        return True
    text = review.strip()
    if len(text) < 6:
        return True
    t = text.lower()
    # If any dish cue appears, don't skip
    if any(cue in t for cue in _DISH_CUES):
        return False
    # If it's dominated by generic terms and no cues, skip
    if any(g in t for g in _GENERIC_KWS):
        return True
    # Default: process (conservative)
    return False

def _extract_dishes_rule_based(text: str) -> list[str]:
    """Rule-based Thai dish detector using a curated list (length-desc sort to prefer longer matches)."""
    if not isinstance(text, str) or not text.strip():
        return []
    t = text.strip()
    curated = [
        "ต้มแซ่บกระดูกอ่อน", "ก้อยเนื้อย่าง", "ยำหอยนางรม", "ปากเป็ดทอด", "ต้มยำกุ้ง",
        "ลาบหมู", "ลาบเป็ด", "ปีกไก่ทอด", "ข้าวผัด", "คอหมูย่าง", "ก้อยเนื้อ",
        "ก้อยขม", "ต้มขม", "ต้มแซ่บ", "ส้มตำ",
    ]
    # prefer longer names first to avoid substring duplicates
    curated = sorted(curated, key=len, reverse=True)
    found = []
    seen = set()
    for name in curated:
        if name in t and name not in seen:
            found.append(name)
            seen.add(name)
    return found

def _build_fallback_entries(restaurant: str, review: str) -> list[dict]:
    dishes = _extract_dishes_rule_based(review) or ["เมนูรวม"]
    return [
        {
            "restaurant": restaurant,
            "dish": d,
            "cuisine": "thai",
            "restriction": None,
            "sentiment": {"positive": [], "negative": []}
        }
        for d in dishes
    ]

def flatten_json_list(json_str):
    # Robust: accept None/NaN/empty/already-parsed and return [] quietly on errors
    if json_str is None:
        return []
    try:
        import math
        if isinstance(json_str, float) and math.isnan(json_str):
            return []
    except Exception:
        pass

    try:
        items = json_str
        if isinstance(json_str, str):
            json_str = json_str.strip()
            if not json_str:
                return []
            items = json.loads(json_str)

        def normalize_item(item: dict):
            sentiment = item.get('sentiment', {})
            if not isinstance(sentiment, dict):
                sentiment = {}
            return {
                'review_id': item.get('review_id', ''),
                'restaurant': item.get('restaurant', ''),
                'dish': item.get('dish', ''),
                'cuisine': item.get('cuisine', ''),
                'restriction': item.get('restriction', ''),
                'sentiment': {
                    'positive': sentiment.get('positive', []) if isinstance(sentiment, dict) else [],
                    'negative': sentiment.get('negative', []) if isinstance(sentiment, dict) else []
                }
            }

        if isinstance(items, list):
            return [normalize_item(i) for i in items if isinstance(i, dict)]
        if isinstance(items, dict):
            return [normalize_item(items)]
        return []
    except Exception:
        return []
        
def clean_json_string(json_str):
    return re.sub(r',\s*([}\]])', r'\1', json_str)

def fix_json_keys(json_str):
    json_str = re.sub(r'//.*|#.*', '', json_str)
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    json_str = re.sub(r"'", '"', json_str)
    json_str = re.sub(r'([{,]\s*)([^\s"\':,{}]+)\s*:', r'\1"\2":', json_str)
    return json_str

def _to_db_int(v):
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    try:
        return int(v)
    except Exception:
        return None

def _to_db_text(v):
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if v is None:
        return None
    return str(v)

def _init_pg_pool() -> bool:
    """Initialize a global connection pool if not already created."""
    global _PG_POOL
    if _PG_POOL is not None:
        return True
    try:
        sslmode = os.environ.get("PG_SSLMODE", "disable")
        _PG_POOL = pg_pool.SimpleConnectionPool(
            minconn=_int_env("PG_POOL_MIN", 1),
            maxconn=_int_env("PG_POOL_MAX", 5),
            host=PG_CONFIG['host'],
            port=PG_CONFIG['port'],
            user=PG_CONFIG['user'],
            password=PG_CONFIG['password'],
            dbname=PG_CONFIG['database'],
            connect_timeout=5,
            sslmode=sslmode,
        )
        return True
    except Exception as e:
        LOGGER.warning("Failed to init PG pool; will use direct connections: %s", e)
        return False

@contextmanager
def with_pg_conn():
    """Context manager yielding a Postgres connection, using pool when available."""
    sslmode = os.environ.get("PG_SSLMODE", "disable")
    # Try pool first
    if _PG_POOL is None:
        _init_pg_pool()
    if _PG_POOL is not None:
        conn = _PG_POOL.getconn()
        try:
            yield conn
        finally:
            try:
                _PG_POOL.putconn(conn)
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
    else:
        # Fallback direct connection
        conn = psycopg2.connect(
            host=PG_CONFIG['host'],
            port=PG_CONFIG['port'],
            user=PG_CONFIG['user'],
            password=PG_CONFIG['password'],
            dbname=PG_CONFIG['database'],
            connect_timeout=5,
            sslmode=sslmode,
        )
        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass


def _pg_writes_enabled() -> bool:
    # Allow disabling writes via env var
    if os.environ.get("PG_WRITE_DISABLED", "0") == "1":
        return False
    return True


def _pg_is_available(cooldown_sec: int = 120) -> bool:
    """Quick health check with cooldown to avoid spamming failed connects."""
    global _PG_AVAILABLE, _PG_LAST_CHECK_TS
    if not _pg_writes_enabled():
        return False
    now = time.time()
    if _PG_AVAILABLE is False and _PG_LAST_CHECK_TS and (now - _PG_LAST_CHECK_TS) < cooldown_sec:
        return False
    try:
        with with_pg_conn() as conn:
            pass
        _PG_AVAILABLE = True
    except Exception as e:
        _PG_AVAILABLE = False
        # Print a concise, one-line diagnosis the first time or after cooldown
        msg = str(e).lower()
        reason = "auth" if "password authentication failed" in msg else (
            "refused" if "connection refused" in msg or "could not connect to server" in msg else (
            "timeout" if "timeout" in msg else "unknown"))
        if reason == "refused":
            LOGGER.warning("Postgres connection refused (host/port/firewall). Will skip writes during cooldown.")
        elif reason == "auth":
            LOGGER.warning("Postgres authentication failed (user/password/db). Skipping writes during cooldown.")
        elif reason == "timeout":
            LOGGER.warning("Postgres connection timed out (network/DNS). Skipping writes during cooldown.")
        else:
            LOGGER.warning("Postgres unavailable (%s): %s", reason, e)
    _PG_LAST_CHECK_TS = now
    return bool(_PG_AVAILABLE)


def _get_or_init_rev_ext_base() -> int:
    """Fetch and cache the current MAX(rev_ext_id) once per run."""
    global REV_EXT_BASE
    if REV_EXT_BASE is not None:
        return REV_EXT_BASE
    try:
        with with_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(MAX(rev_ext_id), 0) FROM review_extracts")
                base = cur.fetchone()[0] or 0
        REV_EXT_BASE = int(base)
    except Exception:
        # If table doesn't exist yet, base is 0 (init_database will create it)
        REV_EXT_BASE = 0
    return REV_EXT_BASE


def init_database():
    """Ensure the legacy review_extracts table (rev_ext_id, source_id, source_type, data_extract) exists."""
    if not _pg_is_available():
        LOGGER.warning("Postgres not reachable; skipping table init and proceeding offline.")
        return
    ddl = """
    CREATE TABLE IF NOT EXISTS review_extracts (
        rev_ext_id BIGINT PRIMARY KEY,
        source_id BIGINT,
        source_type VARCHAR(64) NOT NULL,
        data_extract TEXT
    );
    """
    try:
        with with_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
            conn.commit()
        LOGGER.info("PostgreSQL table 'review_extracts' (legacy schema) is ready")
    except Exception as e:
        LOGGER.warning("PostgreSQL unavailable; proceeding without DB (writes disabled during cooldown)")
        # mark unavailable to avoid repeated attempts
        global _PG_AVAILABLE, _PG_LAST_CHECK_TS
        _PG_AVAILABLE = False
        _PG_LAST_CHECK_TS = time.time()

def upsert_review_extracts_pg(results: list, source_type: str = "web") -> int:
    """Insert/upsert rows into review_extracts (rev_ext_id, source_id, source_type, data_extract).

    - rev_ext_id: uses Row Number
    - source_id: uses Row Number (acts as source-origin id)
    - source_type: provided param (default 'web')
    - data_extract: Extracted JSON string
    Only rows with Status == 'Success' and a non-empty Extracted JSON are written.
    """
    if not results:
        return 0
    if not _pg_is_available():
        # DB offline; skip writing but keep processing
        return 0
    rows = []
    for r in results:
        try:
            if r.get("Status") != "Success":
                continue
        except AttributeError:
            continue
        rn = _to_db_int(r.get("Row Number"))
        if rn is None:
            continue
        data_json = _to_db_text(r.get("Extracted JSON"))
        if data_json is None:
            continue
        rows.append((rn, _to_db_text(source_type) or "web", data_json))

    if not rows:
        return 0

    # Allocate continuous rev_ext_id values starting from current MAX(rev_ext_id)
    base = _get_or_init_rev_ext_base()
    values_with_ids = []
    for i, (source_id, s_type, data_json) in enumerate(rows, start=1):
        values_with_ids.append((base + i, source_id, s_type, data_json))

    try:
        with with_pg_conn() as conn:
            with conn.cursor() as cur:
                pg_extras.execute_values(
                    cur,
                    """
                    INSERT INTO review_extracts (rev_ext_id, source_id, source_type, data_extract)
                    VALUES %s
                    ON CONFLICT (rev_ext_id) DO UPDATE SET
                        source_id = EXCLUDED.source_id,
                        source_type = EXCLUDED.source_type,
                        data_extract = EXCLUDED.data_extract
                    """,
                    values_with_ids,
                    page_size=1000
                )
            conn.commit()
    except Exception as e:
        # mark unavailable and skip further attempts for a bit
        global _PG_AVAILABLE, _PG_LAST_CHECK_TS
        _PG_AVAILABLE = False
        _PG_LAST_CHECK_TS = time.time()
        LOGGER.warning("DB offline; skipping upsert (cooldown active): %s", e)
        return 0
    # Bump the global base so the next call continues
    global REV_EXT_BASE
    REV_EXT_BASE = base + len(values_with_ids)
    return len(values_with_ids)

def store_reviews_extract_to_sql(results: list, source_type: str = "web", _retry=False):
    """Write extracts into legacy review_extracts table (rev_ext_id, source_id, source_type, data_extract)."""
    return upsert_review_extracts_pg(results, source_type=source_type)

# NEW: sync any CSV (checkpoint or final) to SQL: web_review first, then Reviews_extract
def sync_results_csv_to_reviews_extract(csv_path: str, source_type: str = "web") -> int:
    """
    Read a results CSV (checkpoint or final), upsert into web_review,
    then insert/upsert into Reviews_extract. Safe to call multiple times.
    """
    if not os.path.exists(csv_path):
        LOGGER.warning("CSV not found: %s", csv_path)
        return 0
    try:
        df = pd.read_csv(csv_path, keep_default_na=False)
    except Exception as e:
        LOGGER.error("Failed to read CSV %s: %s", csv_path, e)
        return 0

    records = df.to_dict(orient="records")
    if not records:
        LOGGER.info("No records in %s", csv_path)
        return 0

    # Directly upsert into Postgres review_extracts (legacy schema)
    upserted = upsert_review_extracts_pg(records, source_type=source_type)
    LOGGER.info("Synced %s rows from %s into review_extracts (rev_ext_id/source_id/source_type/data_extract)", upserted, csv_path)
    return len(records)

# Utility: re-sync a list of historical CSVs into DB (web_review then Reviews_extract)
def backfill_from_csvs(csv_paths: list[str]):
    total = 0
    for p in csv_paths:
        try:
            total += sync_results_csv_to_reviews_extract(p, source_type="web")
        except Exception as e:
            LOGGER.error("Backfill failed for %s: %s", p, e)
    LOGGER.info("Backfill complete. Total rows synced: %s", total)

# ---------------------------
# Simple TTL Cache for LLM outputs
# ---------------------------
class _TTLCache:
    def __init__(self, max_size: int = 1000, ttl_sec: int = 3600):
        self.max_size = max_size
        self.ttl = ttl_sec
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> str | None:
        now = time.time()
        v = self._store.get(key)
        if not v:
            return None
        ts, val = v
        if now - ts > self.ttl:
            try:
                del self._store[key]
            except Exception:
                pass
            return None
        return val

    def set(self, key: str, value: str):
        now = time.time()
        if len(self._store) >= self.max_size:
            # drop oldest
            oldest_key = min(self._store.items(), key=lambda x: x[1][0])[0]
            try:
                del self._store[oldest_key]
            except Exception:
                pass
        self._store[key] = (now, value)

_LLM_CACHE = _TTLCache(
    max_size=_int_env("OLLAMA_CACHE_MAX", 1000),
    ttl_sec=_int_env("OLLAMA_CACHE_TTL_SEC", 3600),
)

def process_single_row(idx, row):
    try:
        input_data = {
            "restaurant": str(getattr(row, "restaurant_name", "")),
            "review": str(getattr(row, "review_text", ""))
        }
        # Fast-path skip to reduce CPU and heat (toggle with PREFILTER_ENABLED=0)
        if _bool_env("PREFILTER_ENABLED", True) and should_skip_review(input_data["review"], input_data["restaurant"]):
            # Treat as a successful empty extraction to avoid retry churn
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": "[]",
                "Error Message": "Skipped by prefilter"
            }
        # Cache check
        cache_key = f"{input_data['restaurant']}||{input_data['review']}"
        cached = _LLM_CACHE.get(cache_key)
        if cached is not None:
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": cached,
                "Error Message": "cache hit"
            }
        response = chain.invoke(input_data)
        # Handle both dict and str response
        if isinstance(response, dict):
            raw = response.get("text", "").strip()
        elif isinstance(response, str):
            raw = response.strip()
        else:
            raw = ""
        if not raw:
            # Retry once with a stricter JSON-only prompt
            minimal_prompt = PromptTemplate.from_template(
                """
                Return a JSON array of dish insights based on the input.
                If no specific dish names are present, return [] and nothing else.

                Input Restaurant: {restaurant}
                Input Review: {review}

                Output JSON array schema:
                [
                  {{
                    "review_id": <int>,
                    "restaurant": <string>,
                    "dish": <string>,
                    "cuisine": <string|null>,
                    "restriction": <string|null>,
                    "sentiment": {{"positive": [<string>], "negative": [<string>]}}
                  }}
                ]
                """
            )
            retry_raw = (minimal_prompt | llm).invoke(input_data)
            raw = retry_raw.get("text", "").strip() if isinstance(retry_raw, dict) else (retry_raw.strip() if isinstance(retry_raw, str) else "")
            if not raw:
                fb = _build_fallback_entries(input_data["restaurant"], input_data["review"])
                return {
                    "Row Number": idx + 1,
                    "Restaurant Name": input_data["restaurant"],
                    "Review Text": input_data["review"],
                    "Status": "Success",
                    "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                    "Error Message": "fallback: empty output"
                }
        json_str = extract_json(raw)
        if not json_str:
            # Retry once with a stricter JSON-only prompt
            minimal_prompt = PromptTemplate.from_template(
                """
                Return only a valid JSON array (no text). If no dish names are present, return [].
                Input Restaurant: {restaurant}
                Input Review: {review}
                """
            )
            retry_raw = (minimal_prompt | llm).invoke(input_data)
            retry_raw = retry_raw.get("text", "").strip() if isinstance(retry_raw, dict) else (retry_raw.strip() if isinstance(retry_raw, str) else "")
            json_str = extract_json(retry_raw)
            if not json_str:
                fb = _build_fallback_entries(input_data["restaurant"], input_data["review"])
                return {
                    "Row Number": idx + 1,
                    "Restaurant Name": input_data["restaurant"],
                    "Review Text": input_data["review"],
                    "Status": "Success",
                    "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                    "Error Message": "fallback: no json found"
                }
        if not is_balanced_json(json_str):
            fb = _build_fallback_entries(input_data["restaurant"], input_data["review"])
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                "Error Message": "fallback: unbalanced json"
            }
        if has_unterminated_string(json_str):
            fb = _build_fallback_entries(input_data["restaurant"], input_data["review"])
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                "Error Message": "fallback: unterminated string"
            }
        try:
            try:
                json_result = json.loads(json_str)
            except json.JSONDecodeError:
                fixed_json_str = fix_json_keys(json_str)
                fixed_json_str = clean_json_string(fixed_json_str)
                try:
                    json_result = json.loads(fixed_json_str)
                except Exception as e:
                    try:
                        json_result = ast.literal_eval(fixed_json_str)
                    except Exception as e:
                        fb = _build_fallback_entries(input_data["restaurant"], input_data["review"])
                        return {
                            "Row Number": idx + 1,
                            "Restaurant Name": input_data["restaurant"],
                            "Review Text": input_data["review"],
                            "Status": "Success",
                            "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                            "Error Message": f"fallback: invalid json ({str(e)})"
                        }
            # Normalize: ensure dish is a non-empty string; drop invalid entries
            def is_valid_entry(obj):
                try:
                    # normalize keys that might appear in Thai or variants
                    if not isinstance(obj, dict):
                        return False
                    d = obj.get("dish", None) or obj.get("เมนู", None) or obj.get("ชื่อเมนู", None)
                except AttributeError:
                    return False
                if d is None:
                    return False
                if isinstance(d, str):
                    return d.strip() != ""
                return False

            normalized = None
            if isinstance(json_result, list):
                normalized = [o for o in json_result if isinstance(o, dict) and is_valid_entry(o)]
            elif isinstance(json_result, dict):
                normalized = [json_result] if is_valid_entry(json_result) else []
            else:
                normalized = []

            if not normalized:
                # Fallback: rule-based dish extraction; if still empty, emit one generic entry
                fallback_dishes = _extract_dishes_rule_based(input_data["review"]) or ["เมนูรวม"]
                fb = [
                    {
                        "restaurant": input_data["restaurant"],
                        "dish": d,
                        "cuisine": "thai",
                        "restriction": None,
                        "sentiment": {"positive": [], "negative": []}
                    }
                    for d in fallback_dishes
                ]
                return {
                    "Row Number": idx + 1,
                    "Restaurant Name": input_data["restaurant"],
                    "Review Text": input_data["review"],
                    "Status": "Success",
                    "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                    "Error Message": ""
                }

            result_obj = {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(normalized, ensure_ascii=False, indent=2),
                "Error Message": ""
            }
            # store cache
            try:
                _LLM_CACHE.set(cache_key, result_obj["Extracted JSON"])
            except Exception:
                pass
            return result_obj
        except json.JSONDecodeError as e:
            fb = _build_fallback_entries(input_data["restaurant"], input_data["review"])
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                "Error Message": f"fallback: json decode error ({str(e)})"
            }
    except Exception as e:
        fb = _build_fallback_entries(str(getattr(row, "restaurant_name", "")), str(getattr(row, "review_text", "")))
        return {
            "Row Number": idx + 1,
            "Restaurant Name": str(getattr(row, "restaurant_name", "")),
            "Review Text": str(getattr(row, "review_text", "")),
            "Status": "Success",
            "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
            "Error Message": f"fallback: exception ({str(e)})"
        }

def process_rows(
    df: pd.DataFrame,
    checkpoint_path: str = "/Users/mac/Desktop/CSC498 Capstone Project/DishDive/Langchain/Ollama Qwen3/150K/processed_bangkok_restaurant_reviews_checkpoint.csv",
    output_path: str = "/Users/mac/Desktop/CSC498 Capstone Project/DishDive/Langchain/Ollama Qwen3/150K/processed_bangkok_restaurant_reviews.csv",
    expanded_output_path: str = "/Users/mac/Desktop/CSC498 Capstone Project/DishDive/Langchain/Ollama Qwen3/150K/processed_bangkok_restaurant_reviews_expanded.csv",
    batch_size: int = None,
    max_workers: int = None,
    start_from_row_number: int | None = None
) -> list:
    # Allow adaptive tuning via env (with gentle defaults for heat control)
    if batch_size is None:
        batch_size = _int_env("BATCH_SIZE", 50)
    if max_workers is None:
        max_workers = _int_env("MAX_WORKERS", 2)
    processed_indices = set()
    results = []
    web_review_buffer = []  # buffer to flush to web_review every 1000 rows
    error_log = []
    last_error_log_time = datetime.now()
    error_log_interval = timedelta(minutes=5)

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        LOGGER.info("Output file %s does not exist yet; will create at the end.", output_path)
        # Optionally, exit or handle the error here
    else:
        results_df = pd.read_csv(output_path)
        # ...rest of your code...
    
    if os.path.exists(checkpoint_path):
        checkpoint_df = pd.read_csv(checkpoint_path, keep_default_na=False)
        processed_indices = set(checkpoint_df["Row Number"] - 1)
        results = checkpoint_df.to_dict(orient="records")
        LOGGER.info("Resuming from checkpoint, %s rows already processed.", len(processed_indices))
        # Optional: sync checkpoint into DB if available
        if _pg_is_available():
            try:
                sync_results_csv_to_reviews_extract(checkpoint_path, source_type="web")
            except Exception:
                # avoid noisy logs; _pg_is_available already guards cooldown
                pass


    total_rows = len(df)
    rows_to_process = [
        (idx, row)
        for idx, row in enumerate(df.itertuples(index=False))
        if idx not in processed_indices and (start_from_row_number is None or (idx + 1) >= start_from_row_number)
    ]

    processed_count = 0
    batch_count = 0
    LOGGER.info("Starting processing %s restaurants...", len(rows_to_process))
    # Dynamic batch sizing controls
    batch_min = _int_env("BATCH_MIN", max(1, batch_size // 2))
    batch_max = _int_env("BATCH_MAX", max(batch_size, 4))
    target_sec = _float_env("TARGET_BATCH_SEC", 10.0)

    batch_start = 0
    while batch_start < len(rows_to_process):
        batch = rows_to_process[batch_start:batch_start+batch_size]
        start_time = time.time()
        batch_count += 1
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_single_row, idx, row) for idx, row in batch]
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                web_review_buffer.append(result)
                processed_count += 1

                if processed_count % 1000 == 0:
                    LOGGER.info("Progress: %s restaurants processed out of %s", processed_count, len(rows_to_process))
                    # Flush last 1000 rows directly to Postgres review_extracts
                    try:
                        upsert_review_extracts_pg(web_review_buffer)
                        web_review_buffer = []
                    except Exception as e:
                        LOGGER.warning("Failed to upsert %s rows into review_extracts at checkpoint: %s", len(web_review_buffer), e)
                    # Done flushing this 1000, continue

                if isinstance(result, dict):
                    status = result.get("Status")
                    # Only treat true failures as errors; skip benign statuses in the error log
                    if status in ("JSON Not Found", "Unbalanced JSON", "Unterminated String", "Invalid JSON", "Exception", "Empty Output"):
                        error_log.append({
                            "Row Number": result.get("Row Number"),
                            "Error Message": result.get("Error Message"),
                            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

        elapsed = time.time() - start_time
        LOGGER.info("Batch %s processed in %.2f seconds (batch_size=%s, workers=%s)", batch_count, elapsed, batch_size, max_workers)
        checkpoint_df = pd.DataFrame(results)
        checkpoint_df.to_csv(checkpoint_path, index=False)
        LOGGER.info("Checkpoint saved at row %s/%s", min(batch_start+batch_size, len(rows_to_process)), len(rows_to_process))

        # Adjust next batch size toward target duration
        if elapsed < max(1.0, 0.5 * target_sec) and batch_size < batch_max:
            new_size = min(batch_max, max(batch_size + 1, int(batch_size * 1.25)))
            if new_size != batch_size:
                LOGGER.info("Increasing batch size %s -> %s", batch_size, new_size)
                batch_size = new_size
        elif elapsed > 1.5 * target_sec and batch_size > batch_min:
            new_size = max(batch_min, min(batch_size - 1, int(batch_size * 0.8)))
            if new_size != batch_size:
                LOGGER.info("Decreasing batch size %s -> %s", batch_size, new_size)
                batch_size = new_size

        cooldown = _int_env("COOLDOWN_BASE_SEC", 5)
        if cooldown > 0:
            LOGGER.debug("Cooling down for %s seconds...", cooldown)
            time.sleep(cooldown)

        batch_start += len(batch)
    columns = [
        "Row Number",                                                                                                                                                                                                                                                                                                                                                                                                               
        "Restaurant Name",
        "Review Text",
        "Status",
        "Extracted JSON",
        "Error Message"
    ]
    # Flush any remaining rows in the buffer to review_extracts (Postgres)
    if web_review_buffer:
        try:
            upsert_review_extracts_pg(web_review_buffer)
            LOGGER.info("Stored remaining %s rows to review_extracts", len(web_review_buffer))
            web_review_buffer = []
        except Exception as e:
            LOGGER.warning("Failed to store remaining rows to review_extracts: %s", e)

    results_df = pd.DataFrame(results, columns=columns)
    results_df.to_csv(output_path, index=False)
    LOGGER.info("Results exported to %s with clear column names.", output_path)

    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
    LOGGER.info("Processing complete. Check the output files for results.")

    # NEW: final safety sync from the complete output CSV into review_extracts (Postgres)
    if _pg_is_available():
        try:
            sync_results_csv_to_reviews_extract(output_path, source_type="web")
        except Exception:
            # suppress repeated connection errors; cooldown will apply
            pass

    #Print error log ONCE at the end
    if error_log:
        LOGGER.error("--- Error log (%s) ---", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        for err in error_log[-10:]:
            LOGGER.error("Row %s: %s at %s", err['Row Number'], err['Error Message'], err['Time'])
        LOGGER.error("--- End of error log ---")
        
    return results

def _write_data_extract_csv_from_results(results: list, out_csv: str):
    """Write a CSV with a single column 'data_extract' where each cell is
    a JSON object: {"data_extract": [ ... ]} matching requested format.
    """
    out_rows = []
    for r in results:
        ex = r.get("Extracted JSON")
        arr = []
        if isinstance(ex, str) and ex.strip():
            try:
                arr = json.loads(ex)
                if not isinstance(arr, list):
                    arr = []
            except Exception:
                arr = []
        if not arr:
            # synthesize fallback from row info
            rest = r.get("Restaurant Name") or ""
            review = r.get("Review Text") or ""
            arr = _build_fallback_entries(rest, review)
        out_rows.append({"data_extract": json.dumps({"data_extract": arr}, ensure_ascii=False)})
    pd.DataFrame(out_rows).to_csv(out_csv, index=False)

def main():
    _log_config_summary()
    # Load the CSV file and select rows for this run; allow override via env
    input_csv = os.environ.get(
        "INPUT_CSV",
        '/Users/mac/Desktop/CSC498 Capstone Project/DishDive/Scraping/google review/3K/bangkok_restaurant_reviews_dataset-v3.csv'
    )
    try:
        df_full = load_csv(input_csv)
    except Exception as e:
        LOGGER.error("Failed to load input CSV %s: %s", input_csv, e)
        return
    # Process slice bounds from env
    start = _int_env("ROW_START", 100)
    end = _int_env("ROW_END", 2000)
    csv_df = df_full.iloc[start:end].reset_index(drop=True)

    # Initialize database before processing
    init_database()

    # Output directory and paths (env-overridable)
    out_dir = os.environ.get(
        "OUTPUT_DIR",
        "/Users/mac/Desktop/CSC498 Capstone Project/DishDive/Langchain/Ollama Qwen3/150K",
    )
    os.makedirs(out_dir, exist_ok=True)
    out2000 = os.path.join(out_dir, "processed_bangkok_restaurant_reviews_2000.csv")
    cp2000 = os.path.join(out_dir, "processed_bangkok_restaurant_reviews_checkpoint_2000.csv")
    exp2000 = os.path.join(out_dir, "processed_bangkok_restaurant_reviews_expanded_2000.csv")
    data_extract2000 = os.path.join(out_dir, "processed_bangkok_restaurant_reviews_data_extract_2000.csv")

    # For this export, disable prefilter to avoid skipping dish mentions (env overrides allowed)
    if os.environ.get("PREFILTER_ENABLED") is None:
        os.environ["PREFILTER_ENABLED"] = "0"

    results_2000 = process_rows(
        csv_df,
        checkpoint_path=cp2000,
        output_path=out2000,
        expanded_output_path=exp2000,
        batch_size=_int_env("BATCH_SIZE", 25),
        max_workers=_int_env("MAX_WORKERS", 2)
    )
    _write_data_extract_csv_from_results(results_2000, data_extract2000)
    LOGGER.info("Wrote data_extract CSV -> %s", data_extract2000)


if __name__ == "__main__":
    main()