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
import psycopg2
from psycopg2.extras import RealDictCursor

ALIASES = {
    "bbq": ["bbq", "barbecue", "บาร์บีคิว", "บาบีคิว", "ปิ้งย่าง", "หมูกระทะ", "ยากินิคุ", "yakiniku"],
    "shabu": ["ชาบู", "shabu", "hot pot", "hotpot", "หม้อไฟ", "สุกี้"],
    "ramen": ["ราเมง", "ramen"],
    "noodles": ["noodle", "noodles", "ก๋วยเตี๋ยว", "ก๋วยจั๊บ", "pho", "ก๋วยเตี๋ยวเรือ"],
    "sushi": ["sushi", "ซูชิ", "ซาชิมิ", "sashimi"],
    "steak": ["steak", "สเต็ก"],
    "pizza": ["pizza", "พิซซ่า"],
    "burger": ["burger", "hamburger", "เบอร์เกอร์"],
    "seafood": ["seafood", "ซีฟู้ด", "ทะเล"],
    "dimsum": ["dimsum", "ติ่มซำ"],
    "fried_chicken": ["fried chicken", "ไก่ทอด", "คาราอะเกะ", "karaage"],
    "taco": ["taco", "tacos"],
    "cafe": ["cafe", "คาเฟ่", "กาแฟ"],
    "bakery": ["bakery", "เค้ก", "ขนม"],
}

PRIORITY = [
    "bbq", "shabu", "ramen", "sushi", "pizza", "burger", "steak", "dimsum",
    "noodles", "seafood", "fried_chicken", "taco", "cafe", "bakery"
]

TOKEN_PAT = re.compile(r"[\wก-๙]+", re.UNICODE)


def score_match(name: str, term: str) -> float:
    n = name.lower()
    t = term.lower()
    if t in n:
        # word-boundary boost when clearly separated
        if re.search(rf"\b{re.escape(t)}\b", n):
            return 1.0
        return 0.8
    return 0.0


def choose_tag(name: str):
    name = name.lower()
    best_tag, best_score = None, 0.0
    for tag in PRIORITY:
        terms = ALIASES.get(tag, [])
        tag_score = max((score_match(name, term) for term in terms), default=0.0)
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
