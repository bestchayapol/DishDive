import json
import re
import time
from typing import List, Dict

# Prefilter keyword sets
GENERIC_KWS = set([
    "บริการ", "พนักงาน", "ราคา", "บรรยากาศ", "สะอาด", "คิว", "ที่จอด", "เพลง", "รอ", "รวดเร็ว",
    "service", "staff", "price", "ambience", "parking", "clean", "queue",
])
DISH_CUES = set([
    "ต้ม", "ผัด", "ทอด", "แกง", "ยำ", "ตำ", "ก๋วยเตี๋ยว", "ข้าว", "ซุป", "ซูชิ", "ราเมง",
    "พิซซ่า", "สเต๊ก", "ส้มตำ", "ต้มยำ", "ไก่", "หมู", "กุ้ง", "ปลา", "พาสต้า", "เบอร์เกอร์",
    "pizza", "sushi", "ramen", "steak", "tom yum", "noodle", "fried", "soup", "pasta", "burger",
])


def should_skip_review(review: str, restaurant: str | None = None) -> bool:
    if not isinstance(review, str):
        return True
    text = review.strip()
    if len(text) < 6:
        return True
    t = text.lower()
    if any(cue in t for cue in DISH_CUES):
        return False
    if any(g in t for g in GENERIC_KWS):
        return True
    return False


def clean_model_output(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def is_balanced_json(s: str) -> bool:
    stack = []
    pairs = {'{': '}', '[': ']'}
    for c in s:
        if c in pairs:
            stack.append(pairs[c])
        elif c in pairs.values():
            if not stack or c != stack.pop():
                return False
    return not stack


def has_unterminated_string(json_str: str) -> bool:
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
    if cleaned:
        try:
            json.loads(cleaned)
            return cleaned
        except Exception:
            pass
    match_array = re.search(r'\[\s*(?:\{.*?\}\s*(?:,\s*\{.*?\}\s*)*)?\]', cleaned, re.DOTALL)
    if match_array:
        return match_array.group(0)
    match_obj = re.search(r'\{.*?\}', cleaned, re.DOTALL)
    if match_obj:
        return match_obj.group(0)
    return ""


def fix_json_keys(json_str: str) -> str:
    json_str = re.sub(r'//.*|#.*', '', json_str)
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    json_str = re.sub(r"'", '"', json_str)
    json_str = re.sub(r'([{,]\s*)([^\s"\':,{}]+)\s*:', r'\1"\2":', json_str)
    return json_str


def clean_json_string(json_str: str) -> str:
    return re.sub(r',\s*([}\]])', r'\1', json_str)


def extract_dishes_rule_based(text: str) -> List[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    t = text.strip()
    curated = [
        "ต้มแซ่บกระดูกอ่อน", "ก้อยเนื้อย่าง", "ยำหอยนางรม", "ปากเป็ดทอด", "ต้มยำกุ้ง",
        "ลาบหมู", "ลาบเป็ด", "ปีกไก่ทอด", "ข้าวผัด", "คอหมูย่าง", "ก้อยเนื้อ",
        "ก้อยขม", "ต้มขม", "ต้มแซ่บ", "ส้มตำ",
    ]
    curated = sorted(curated, key=len, reverse=True)
    found = []
    seen = set()
    for name in curated:
        if name in t and name not in seen:
            found.append(name)
            seen.add(name)
    return found


def build_fallback_entries(restaurant: str, review: str) -> list[dict]:
    dishes = extract_dishes_rule_based(review) or ["เมนูรวม"]
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


class TTLCache:
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
            oldest_key = min(self._store.items(), key=lambda x: x[1][0])[0]
            try:
                del self._store[oldest_key]
            except Exception:
                pass
        self._store[key] = (now, value)
