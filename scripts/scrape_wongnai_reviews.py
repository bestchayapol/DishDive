#!/usr/bin/env python
"""Scrape recent reviews for a given list of Wongnai restaurant slugs.

Usage examples:

  python scripts/scrape_wongnai_reviews.py --slugs file:restaurant_slugs.txt --limit-per 40 --out out_wongnai_reviews.csv
  python scripts/scrape_wongnai_reviews.py --slugs somtum-udon,absorn-thai-bistro --since-days 30

Inputs:
  --slugs          Comma separated list of Wongnai slugs OR 'file:<path>' pointing to a text file (one slug per line).
  --since-days     Only include reviews whose datetime is within the last N days (default: 90).
  --limit-per      Max number of reviews to fetch per restaurant (best-effort; default 50).
  --delay          Base delay seconds between page requests for politeness (default 1.2). Jitter added automatically.
  --out            Output CSV path (default: wongnai_reviews.csv).
  --append         If set, append to existing CSV instead of overwriting.
  --raw-json       If set, also write a JSON lines dump next to CSV (same basename with .jsonl).

Output columns:
  restaurant_slug, review_id, user_name, rating, review_text, created_at, like_count, reply_count, url

Note: This script performs simple HTML parsing; Wongnai could change markup at any time. It does NOT execute JavaScript.
If dynamic loading hides reviews, consider using Wongnai's internal JSON embedded in pages (some pages embed a window.__NUXT__ payload).

Politeness: The script throttles requests. Adjust --delay higher if scraping many restaurants. Avoid hammering the site.

"""
from __future__ import annotations

import argparse
import csv
import os
import random
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator, Iterable, List, Optional

import requests
from bs4 import BeautifulSoup  # type: ignore

# Minimal dependency guard: if bs4 not installed, instruct user.
try:  # noqa: SIM105
    from bs4 import BeautifulSoup  # type: ignore
except Exception as e:  # pragma: no cover
    print("BeautifulSoup4 required. Install with: pip install beautifulsoup4", file=sys.stderr)
    raise

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "th,en-US;q=0.9,en;q=0.8"}
BASE_URL = "https://www.wongnai.com/restaurants/{slug}"

REVIEW_BLOCK_SELECTOR = "div.reviewItem__Wrapper-sc"  # fallback fuzzy match
DATETIME_REGEX = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:.+?Z)")

@dataclass
class Review:
    restaurant_slug: str
    review_id: str
    user_name: str
    rating: Optional[float]
    review_text: str
    created_at: datetime
    like_count: Optional[int]
    reply_count: Optional[int]
    url: str

    def to_row(self):  # CSV row
        return [
            self.restaurant_slug,
            self.review_id,
            self.user_name,
            self.rating if self.rating is not None else "",
            self.review_text.replace("\n", " ").strip(),
            self.created_at.isoformat(),
            self.like_count if self.like_count is not None else "",
            self.reply_count if self.reply_count is not None else "",
            self.url,
        ]


def parse_args():
    ap = argparse.ArgumentParser(description="Scrape Wongnai reviews for given slugs")
    ap.add_argument("--slugs", required=True, help="Comma list of slugs or file:<path> one per line")
    ap.add_argument("--since-days", type=int, default=90, help="Only include reviews newer than N days")
    ap.add_argument("--limit-per", type=int, default=50, help="Max reviews per restaurant")
    ap.add_argument("--delay", type=float, default=1.2, help="Base delay seconds between fetches")
    ap.add_argument("--out", default="wongnai_reviews.csv", help="Output CSV path")
    ap.add_argument("--append", action="store_true", help="Append instead of overwrite")
    ap.add_argument("--raw-json", action="store_true", help="Also write JSONL of raw parsed objects")
    return ap.parse_args()


def load_slugs(spec: str) -> List[str]:
    if spec.startswith("file:"):
        path = Path(spec.split(":",1)[1])
        return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")] 
    return [s.strip() for s in spec.split(",") if s.strip()]


def fetch_html(url: str, delay: float) -> Optional[str]:
    try:
        time.sleep(delay + random.uniform(0, delay*0.3))
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        return resp.text
    except Exception:
        return None


def extract_reviews(slug: str, html: str) -> List[Review]:
    soup = BeautifulSoup(html, "html.parser")

    # Strategy 1: Look for script JSON (Nuxt SSR) which often contains review edges
    reviews: List[Review] = []
    json_hits = []
    for script in soup.find_all("script"):
        txt = script.string or ""
        if "review" in txt.lower() and "createdAt" in txt:
            json_hits.append(txt)
    # This is a heuristic; for brevity we keep HTML extraction as primary.

    # Strategy 2: Parse visible review blocks
    # Wongnai often uses data-test attributes; fallback to class prefix scanning
    candidates = []
    for div in soup.find_all("div"):
        cls = " ".join(div.get("class", []))
        if "review" in cls.lower() and ("rating" in cls.lower() or "wrapper" in cls.lower()):
            candidates.append(div)

    seen_ids: set[str] = set()
    for block in candidates:
        # Extract review id (data attribute or hash of content)
        rid = block.get("data-review-id") or None
        body_text = block.get_text(" \n ").strip()
        if not rid:
            rid = f"auto_{abs(hash(body_text))}"  # fallback
        if rid in seen_ids:
            continue
        seen_ids.add(rid)

        # Rating (look for digits like 4.0/5 or pattern)
        rating = None
        m = re.search(r"(\d(?:\.\d)?)\s*/\s*5", body_text)
        if m:
            try:
                rating = float(m.group(1))
            except ValueError:
                pass

        # Datetime: try ISO in attributes
        created = None
        iso_attr = None
        for time_tag in block.find_all("time"):
            iso_attr = time_tag.get("datetime")
            if iso_attr:
                break
        if iso_attr:
            try:
                created = datetime.fromisoformat(iso_attr.replace("Z", "+00:00"))
            except Exception:
                created = None
        if not created:
            # Fallback regex (any ISO-like in text)
            m2 = DATETIME_REGEX.search(body_text)
            if m2:
                try:
                    created = datetime.fromisoformat(m2.group(1).replace("Z", "+00:00"))
                except Exception:
                    created = None
        if not created:
            # As last resort, mark now (so since-days filtering likely keeps or discards accordingly)
            created = datetime.now(timezone.utc)

        # Username (search for patterns like @ or preceding rating star text)
        user_name = ""
        user_tag = block.find(lambda t: t.name in ("a","span") and t.get("href","").startswith("/users"))
        if user_tag:
            user_name = user_tag.get_text(strip=True)
        if not user_name:
            # heuristic: first line maybe user handle
            first_line = body_text.splitlines()[0] if body_text else ""
            if 0 < len(first_line) <= 40:
                user_name = first_line

        # Extract the main review text (remove rating/username heuristically). Use last paragraph-ish lines.
        lines = [ln.strip() for ln in body_text.splitlines() if ln.strip()]
        review_text = ""
        if len(lines) >= 2:
            review_text = " ".join(lines[1:])
        elif lines:
            review_text = lines[0]

        # Like / reply counts (heuristic digits near 'like' or reply icons)
        like_count = None
        reply_count = None
        m_like = re.search(r"(\d+)\s*(?:likes?|ถูกใจ)", body_text, re.IGNORECASE)
        if m_like:
            like_count = int(m_like.group(1))
        m_reply = re.search(r"(\d+)\s*(?:repl(?:y|ies)|ตอบกลับ)", body_text, re.IGNORECASE)
        if m_reply:
            reply_count = int(m_reply.group(1))

        reviews.append(
            Review(
                restaurant_slug=slug,
                review_id=rid,
                user_name=user_name or "unknown",
                rating=rating,
                review_text=review_text,
                created_at=created,
                like_count=like_count,
                reply_count=reply_count,
                url=BASE_URL.format(slug=slug)+"#reviews",
            )
        )

    return reviews


def filter_and_trim(reviews: List[Review], since_days: int, limit_per: int) -> List[Review]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    # Sort newest first
    reviews.sort(key=lambda r: r.created_at, reverse=True)
    filtered = [r for r in reviews if r.created_at >= cutoff]
    return filtered[:limit_per]


def write_output(path: str, reviews: List[Review], append: bool, write_json: bool):
    if not reviews:
        print("No reviews scraped.")
        return
    header = ["restaurant_slug","review_id","user_name","rating","review_text","created_at","like_count","reply_count","url"]
    mode = "a" if append and Path(path).exists() else "w"
    with open(path, mode, newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if mode == "w":
            w.writerow(header)
        for r in reviews:
            w.writerow(r.to_row())
    if write_json:
        jpath = Path(path).with_suffix(".jsonl")
        with open(jpath, "a" if append else "w", encoding="utf-8") as jf:
            for r in reviews:
                import json as _json
                jf.write(_json.dumps(asdict(r), ensure_ascii=False) + "\n")
    print(f"Wrote {len(reviews)} reviews to {path}")


def main():
    args = parse_args()
    slugs = load_slugs(args.slugs)
    all_reviews: List[Review] = []
    for slug in slugs:
        url = BASE_URL.format(slug=slug)
        html = fetch_html(url, args.delay)
        if not html:
            print(f"WARN: failed to fetch {slug}")
            continue
        reviews = extract_reviews(slug, html)
        clean = filter_and_trim(reviews, args.since_days, args.limit_per)
        all_reviews.extend(clean)
        print(f"{slug}: scraped {len(reviews)} raw -> {len(clean)} kept")
    write_output(args.out, all_reviews, args.append, args.raw_json)

if __name__ == "__main__":
    main()
