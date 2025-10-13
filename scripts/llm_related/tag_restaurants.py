#!/usr/bin/env python
"""
Rule-based tagger for restaurants.image_tag.
- Reads restaurants from Postgres
- Suggests tags based on restaurant name (Thai+EN synonyms)
- Dry-run by default; use --apply to write restaurants.image_tag

Env vars: PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE
"""
import os
import re
import sys
import argparse
import unicodedata
import psycopg2
from psycopg2.extras import RealDictCursor

# Optional Thai helpers
try:  # best-effort; script works without these
    from pythainlp.util import normalize as thai_normalize  # type: ignore
    from pythainlp import word_tokenize as thai_word_tokenize  # type: ignore
except Exception:  # pragma: no cover
    thai_normalize = None  # type: ignore
    thai_word_tokenize = None  # type: ignore

ALIASES = {
    # Grilled/barbecue
    "bbq": [
        "bbq", "barbecue", "บาร์บีคิว", "บาบีคิว", "ปิ้งย่าง", "หมูกระทะ", "ยากินิคุ", "yakiniku",
        "grill", "กริลล์"
    ],
    # Hotpot/shabu/suki
    "shabu": [
        "ชาบู", "shabu", "hot pot", "hotpot", "หม้อไฟ", "สุกี้", "สุกี้ชาบู", "ชาบูชาบู"
    ],
    # Japanese noodles
    "ramen": ["ราเมง", "ramen", "ราเมน", "ラーメン"],
    "udon": ["อุด้ง", "อุด้ง", "udon"],
    "soba": ["โซบะ", "soba"],
    # Sushi/sashimi
    "sushi": ["sushi", "ซูชิ", "ซาชิมิ", "sashimi", "โอมากาเสะ", "omakase"],
    # Fried/Japanese sides often in ramen/izakaya shops
    "fried_chicken": ["fried chicken", "ไก่ทอด", "คาราอะเกะ", "karaage"],
    "katsu": ["คัตสึ", "ทงคัตสึ", "tonkatsu", "katsu"],
    "tempura": ["เทมปุระ", "tempura"],
    "gyoza": ["เกี๊ยวซ่า", "เกี๊ยวซา", "เกี๊ยว", "gyoza", "dumpling"],
    # Other popular Japan/Asia categories
    "yakitori": ["ยากิโทริ", "yakitori"],
    "izakaya": ["อิซากายะ", "izakaya"],
    # Western fast-casual
    "steak": ["steak", "สเต็ก"],
    "pizza": ["pizza", "พิซซ่า"],
    "burger": ["burger", "hamburger", "เบอร์เกอร์"],
    # Chinese/Dim sum
    "dimsum": ["dimsum", "ติ่มซำ", "ติ๋มซำ"],
    # Thai noodles / generic noodles
    "noodles": ["noodle", "noodles", "ก๋วยเตี๋ยว", "ก๋วยจั๊บ", "pho", "ก๋วยเตี๋ยวเรือ", "เฝอ"],
    # Seafood & others
    "seafood": ["seafood", "ซีฟู้ด", "อาหารทะเล", "ทะเล"],
    "taco": ["taco", "tacos"],
    # Cafes/bakeries
    "cafe": ["cafe", "คาเฟ่", "กาแฟ", "คอฟฟี่", "coffee"],
    "bakery": ["bakery", "เค้ก", "ขนม", "เบเกอรี่", "patisserie"],
}

PRIORITY = [
    # High specificity first
    "omakase" if "omakase" in ALIASES else "sushi",
    "izakaya", "yakitori", "gyoza", "katsu", "tempura",
    # Core meal types
    "bbq", "shabu", "ramen", "udon", "soba", "sushi",
    # Western fast-casual
    "pizza", "burger", "steak",
    # Regional/other
    "dimsum", "noodles", "seafood",
    # Light fare / hangouts
    "fried_chicken", "taco", "cafe", "bakery"
]

TOKEN_PAT = re.compile(r"[\wก-๙]+", re.UNICODE)


def _strip_combining(s: str) -> str:
    # Remove combining marks (Thai diacritics included)
    return ''.join(ch for ch in unicodedata.normalize('NFKD', s) if not unicodedata.combining(ch))


def normalize_text(s: str) -> str:
    s = s or ""
    s = s.strip()
    # Thai normalization if available
    if thai_normalize is not None:
        try:
            s = thai_normalize(s)
        except Exception:
            pass
    s = _strip_combining(s)
    s = s.lower()
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)
    return s


def tokenize_name(name: str) -> list:
    n = normalize_text(name)
    # Prefer Thai word segmentation if available; falls back to regex tokens
    if thai_word_tokenize is not None:
        try:
            toks = [t.strip() for t in thai_word_tokenize(n, keep_whitespace=False) if t and not t.isspace()]
        except Exception:
            toks = TOKEN_PAT.findall(n)
    else:
        toks = TOKEN_PAT.findall(n)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for t in toks:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def score_match(tokens: list, normalized_name: str, term: str) -> float:
    """Score how strongly a term matches the name using tokens + fallback substr.

    Heuristics:
    - Exact token match -> 1.0
    - Substring match with clear separators -> 0.9
    - Loose substring -> 0.75
    - No match -> 0
    """
    t = normalize_text(term)
    if not t:
        return 0.0
    if t in tokens:
        return 1.0
    # Safe word boundaries for Latin; Thai lacks spaces, rely on token presence already
    if re.search(rf"\b{re.escape(t)}\b", normalized_name):
        return 0.9
    if t in normalized_name:
        return 0.75
    return 0.0


def choose_tag(name: str):
    # Normalize and tokenize once
    n = normalize_text(name)
    tokens = tokenize_name(n)
    best_tag, best_score = None, 0.0
    # If multiple signals for a tag appear, slightly boost the tag
    for tag in PRIORITY:
        terms = ALIASES.get(tag, [])
        if not terms:
            continue
        scores = [score_match(tokens, n, term) for term in terms]
        tag_score = 0.0
        if scores:
            m = max(scores)
            # small boost for multiple distinct hits
            distinct_hits = sum(1 for s in scores if s >= 0.9)
            tag_score = m + min(0.1 * max(0, distinct_hits - 1), 0.2)
        if tag_score > best_score + 1e-6:
            best_tag, best_score = tag, tag_score
    return best_tag, best_score


def get_conn():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "postgres"),
        dbname=os.getenv("PG_DATABASE", "postgres"),
    )


def main():
    ap = argparse.ArgumentParser(description="Tag restaurants by name")
    ap.add_argument("--limit", type=int, default=0, help="Limit number of restaurants (0=all)")
    ap.add_argument("--apply", action="store_true", help="Write image_tag back to restaurants")
    ap.add_argument("--min-score", type=float, default=0.8, help="Min score to accept a tag; else default")
    ap.add_argument("--export", type=str, default="", help="Optional CSV export path")
    args = ap.parse_args()

    import csv
    rows = []

    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            sql = "SELECT res_id, res_name, res_cuisine, image_tag FROM restaurants ORDER BY res_id"
            if args.limit > 0:
                sql += " LIMIT %s"
                cur.execute(sql, (args.limit,))
            else:
                cur.execute(sql)
            restaurants = cur.fetchall()

        updates = []
        for r in restaurants:
            rid = r["res_id"]
            name = r["res_name"] or ""
            current = r.get("image_tag")
            tag, score = choose_tag(name)
            chosen = tag if (tag and score >= args.min_score) else None
            rows.append({
                "res_id": rid,
                "res_name": name,
                "current_tag": current or "",
                "proposed_tag": chosen or "default",
                "score": f"{score:.2f}",
            })
            if args.apply:
                if chosen != (current or None):
                    updates.append((chosen, rid))

        if args.apply and updates:
            with conn.cursor() as cur:
                cur.executemany("UPDATE restaurants SET image_tag = %s WHERE res_id = %s", updates)
            conn.commit()
            print(f"Applied {len(updates)} tag updates")

    if args.export:
        with open(args.export, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["res_id","res_name","current_tag","proposed_tag","score"])
            w.writeheader()
            w.writerows(rows)
        print(f"Exported {len(rows)} rows to {args.export}")
    else:
        # show sample
        for row in rows[:20]:
            print(row)


if __name__ == "__main__":
    sys.exit(main() or 0)
