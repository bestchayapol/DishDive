#!/usr/bin/env python
from __future__ import annotations

from playwright.sync_api import sync_playwright
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
    "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT, 
    "Accept-Language": "th,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0"
}
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
    ap.add_argument("--slugs", required=False, help="Comma list of slugs or file:<path> one per line")
    ap.add_argument("--since-days", type=int, default=90, help="Only include reviews newer than N days")
    ap.add_argument("--limit-per", type=int, default=50, help="Max reviews per restaurant")
    ap.add_argument("--delay", type=float, default=1.2, help="Base delay seconds between fetches")
    ap.add_argument("--out", default="../wongnai_reviews.csv", help="Output CSV path")
    ap.add_argument("--append", action="store_true", help="Append instead of overwrite")
    ap.add_argument("--raw-json", action="store_true", help="Also write JSONL of raw parsed objects")
    ap.add_argument("--review-url", help="Fetch a single review page URL directly (overrides --slugs)")
    ap.add_argument("--skip-existing-csv", action="store_true", help="Skip review_ids already present in existing CSV (dedupe)")
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

    # Use Playwright to render and extract reviews
    reviews = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-first-run',
                '--disable-default-apps'
            ]
        )
        page = browser.new_page()
        
        # Add anti-bot detection measures
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        # Set realistic user agent and viewport
        page.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36')
        page.set_viewport_size({'width': 1920, 'height': 1080})
        
        url = BASE_URL.format(slug=slug) + "/reviews"
        print(f"DEBUG: Navigating to {url}")
        page.goto(url)
        
        # Wait a bit for page to load
        page.wait_for_timeout(3000)
        print(f"DEBUG: Page loaded, title: {page.title()}")
        
        # Try multiple selector strategies
        selectors_to_try = [
            "div[class*=review]",
            "[data-testid*=review]",
            ".review",
            "[class*=Review]",
            "article",
            "div[class*=comment]",
            "div[class*=item]"
        ]
        
        review_blocks = []
        for selector in selectors_to_try:
            blocks = page.query_selector_all(selector)
            print(f"DEBUG: Selector '{selector}' found {len(blocks)} elements")
            if blocks:
                review_blocks = blocks
                print(f"DEBUG: Using selector '{selector}' with {len(blocks)} elements")
                break
        
        if not review_blocks:
            print("DEBUG: No review blocks found with any selector, dumping page content...")
            print("DEBUG: Page content length:", len(page.content()))
            print("DEBUG: First 1000 chars of page:", page.content()[:1000])
            # Keep browser open for manual inspection
            input("Press Enter to continue after inspecting the browser...")
        
        print(f"DEBUG: Processing {len(review_blocks)} review blocks")
        for i, block in enumerate(review_blocks):
            print(f"DEBUG: Processing review block {i+1}/{len(review_blocks)}")
            # Username
            user_selectors = ["a[href^='/users']", "span[href^='/users']", "[class*=user]", "[class*=author]", "a", "span"]
            user_name = "unknown"
            for user_sel in user_selectors:
                user_elem = block.query_selector(user_sel)
                if user_elem:
                    user_text = user_elem.inner_text().strip()
                    if user_text and len(user_text) < 100:
                        user_name = user_text
                        print(f"DEBUG: Found username '{user_name}' with selector '{user_sel}'")
                        break
            
            # Rating
            rating = None
            star_selectors = ["span[class*=star]", "[class*=rating]", "[class*=score]"]
            for star_sel in star_selectors:
                star_tag = block.query_selector(star_sel)
                if star_tag:
                    try:
                        rating_text = star_tag.inner_text().strip()
                        rating = float(rating_text)
                        print(f"DEBUG: Found rating '{rating}' with selector '{star_sel}'")
                        break
                    except Exception:
                        continue
            
            # Title
            title_selectors = ["b", "strong", "h1", "h2", "h3", "[class*=title]", "[class*=header]"]
            title = ""
            for title_sel in title_selectors:
                title_tag = block.query_selector(title_sel)
                if title_tag:
                    title_text = title_tag.inner_text().strip()
                    if title_text and len(title_text) < 200:
                        title = title_text
                        print(f"DEBUG: Found title '{title}' with selector '{title_sel}'")
                        break
            
            # Review text
            text_selectors = ["p", "div", "span"]
            review_text = ""
            for text_sel in text_selectors:
                p_tags = block.query_selector_all(text_sel)
                if p_tags:
                    texts = [p.inner_text().strip() for p in p_tags if p.inner_text().strip()]
                    if texts:
                        review_text = "\n".join(texts)
                        print(f"DEBUG: Found review text ({len(review_text)} chars) with selector '{text_sel}'")
                        break
            
            print(f"DEBUG: Block {i+1} - user: '{user_name}', rating: {rating}, title: '{title[:50]}...', text: '{review_text[:100]}...'")
            
            if not review_text and not title:
                print(f"DEBUG: Block {i+1} has no content, dumping HTML:")
                print(block.inner_html()[:500])
            # 'อ่านต่อ' link
            more_link = block.query_selector("a:text('อ่านต่อ'), a:text('Read more')")
            if more_link:
                full_url = more_link.get_attribute("href")
                if full_url and "/reviews/" in full_url:
                    if full_url.startswith("/reviews/"):
                        full_url = f"https://www.wongnai.com{full_url}"
                    page2 = browser.new_page()
                    page2.goto(full_url)
                    page2.wait_for_selector("p")
                    full_p = page2.query_selector_all("p")
                    if full_p:
                        review_text = "\n".join([p.inner_text().strip() for p in full_p])
                    page2.close()
            # Datetime
            created = datetime.now(timezone.utc)
            time_tag = block.query_selector("time")
            if time_tag:
                iso_attr = time_tag.get_attribute("datetime")
                if iso_attr:
                    try:
                        created = datetime.fromisoformat(iso_attr.replace("Z", "+00:00"))
                    except Exception:
                        pass
            # Like / reply counts
            like_count = None
            reply_count = None
            like_tag = block.query_selector("span:text('ถูกใจ'), span:text('Like')")
            if like_tag:
                m_like = re.search(r"(\d+)", like_tag.inner_text())
                if m_like:
                    like_count = int(m_like.group(1))
            reply_tag = block.query_selector("span:text('ตอบกลับ'), span:text('Comment')")
            if reply_tag:
                m_reply = re.search(r"(\d+)", reply_tag.inner_text())
                if m_reply:
                    reply_count = int(m_reply.group(1))
            # Review ID
            rid = block.get_attribute("data-review-id") or "auto_" + str(abs(hash(review_text)))
            reviews.append(Review(
                restaurant_slug=slug,
                review_id=rid,
                user_name=user_name,
                rating=rating,
                review_text=(title + "\n" + review_text).strip() if title else review_text.strip(),
                created_at=created,
                like_count=like_count,
                reply_count=reply_count,
                url=url,
            ))
        browser.close()

    return reviews


def extract_review_page(url: str, delay: float) -> List[Review]:
    """Extract reviews from a Wongnai restaurant reviews page.
    This function:
    1. Navigates to the restaurant reviews listing page
    2. Finds individual review links 
    3. Visits each review's dedicated page
    4. Extracts full review content from the dedicated page
    """
    time.sleep(delay + random.uniform(0, delay*0.3))
    
    reviews = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        print(f"DEBUG: Navigating to restaurant reviews page: {url}")
        page.goto(url)
        
        # Wait for page to load
        page.wait_for_timeout(3000)
        print(f"DEBUG: Page loaded, title: {page.title()}")
        
        # Step 1: Find individual review links on the listing page
        # Based on your XPath: /html/body/div[1]/div/div/div[1]/div[3]/div[2]/div[2]/div[1]/div[5]/div/div[3]/div[2]/div/div[1]/a
        review_link_selectors = [
            # Direct links to individual reviews (both /reviews/ and reviews/ patterns)
            "a[href*='reviews/']",
            "a[href*='/reviews/']", 
            # Try in the review container area you identified
            "div:nth-child(3) > div:nth-child(2) > div a[href*='reviews/']",
            "div:nth-child(5) > div > div:nth-child(3) > div:nth-child(2) > div a[href*='reviews/']",
            # More general approaches
            "[href*='reviews/']",
            "[href*='/reviews/']",
            "div[class*=card] a[href*='reviews/']",
            "div[class*=review] a[href*='reviews/']"
        ]
        
        all_review_links = []
        
        # Keep clicking "load more" until no more reviews load
        for page_num in range(10):  # Max 10 pagination attempts
            # Get current review links
            current_links = []
            for selector in review_link_selectors:
                links = page.query_selector_all(selector)
                print(f"DEBUG: Page {page_num + 1} - Selector '{selector}' found {len(links)} review links")
                if links:
                    # Get href attributes
                    for link in links:
                        href = link.get_attribute("href")
                        if href and "reviews/" in href:
                            if href.startswith("/"):
                                href = f"https://www.wongnai.com{href}"
                            elif not href.startswith("http"):
                                href = f"https://www.wongnai.com/{href}"
                            current_links.append(href)
                    break
            
            # Check if we got new links
            new_links = [link for link in current_links if link not in all_review_links]
            if new_links:
                all_review_links.extend(new_links)
                print(f"DEBUG: Found {len(new_links)} new review links on page {page_num + 1}")
            else:
                if page_num > 0:  # Only stop if we tried at least once
                    print(f"DEBUG: No new links found on page {page_num + 1}, stopping")
                    break
            
            # Try to find and click "view more" button
            load_more_button = None
            load_more_selectors = [
                "button:has-text('เพิ่มเติม')",
                "button:has-text('ดูรีวิวเพิ่มเติม')",
                "button:has-text('view more')",
                "a button",
                "[class*=more] button"
            ]
            
            for selector in load_more_selectors:
                try:
                    button = page.query_selector(selector)
                    if button and button.is_visible():
                        load_more_button = button
                        print(f"DEBUG: Found load more button: {selector}")
                        break
                except:
                    continue
            
            if load_more_button:
                try:
                    print(f"DEBUG: Clicking load more button on page {page_num + 1}")
                    load_more_button.click()
                    page.wait_for_timeout(2000)  # Wait 2 seconds for content to load
                except Exception as e:
                    print(f"DEBUG: Failed to click load more: {e}")
                    break
            else:
                print(f"DEBUG: No load more button found, stopping at page {page_num + 1}")
                break
        
        # Remove duplicates
        review_links = list(set(all_review_links))
        print(f"DEBUG: Found {len(review_links)} unique review links total")
        
        if not review_links:
            print("DEBUG: No review links found, trying to inspect page structure...")
            # Show all links for debugging
            all_links = page.query_selector_all("a")
            print(f"DEBUG: Found {len(all_links)} total links on page")
            for i, link in enumerate(all_links[:10]):  # Show first 10
                href = link.get_attribute("href") or ""
                text = link.inner_text().strip()[:50]
                print(f"DEBUG: Link {i+1}: '{href}' -> '{text}'")
            input("Press Enter to continue after inspecting the browser...")
            browser.close()
            return reviews
        
        # Step 2: Visit each individual review page and extract full content
        seen_duplicates = set()  # Track duplicates using username + content hash
        
        for i, review_link in enumerate(review_links):  # Process all found review links
            print(f"DEBUG: Processing review {i+1}/{len(review_links)}: {review_link}")
            
            try:
                # Open individual review page
                review_page = browser.new_page()
                review_page.goto(review_link)
                review_page.wait_for_timeout(2000)
                
                # Extract full review content from dedicated page
                review_data = extract_individual_review_content(review_page, review_link)
                if review_data:
                    # Check for duplicates using username + content hash
                    import hashlib
                    username = review_data.user_name or ''
                    review_text = review_data.review_text or ''
                    
                    # Create hash of username + first 200 chars of review (for duplicate detection)
                    duplicate_key = f"{username}:{review_text[:200]}"
                    content_hash = hashlib.md5(duplicate_key.encode('utf-8')).hexdigest()
                    
                    if content_hash not in seen_duplicates:
                        seen_duplicates.add(content_hash)
                        reviews.append(review_data)
                        print(f"DEBUG: Successfully extracted unique review from {review_link} (user: {username})")
                    else:
                        print(f"DEBUG: Skipped duplicate review from {review_link} (user: {username})")
                else:
                    print(f"DEBUG: Failed to extract content from {review_link}")
                
                review_page.close()
                
                # Add delay between requests
                time.sleep(delay + random.uniform(0, delay*0.3))
                
            except Exception as e:
                print(f"DEBUG: Error processing {review_link}: {e}")
                continue
        
        browser.close()
    
    return reviews


def extract_individual_review_content(page, review_url: str) -> Optional[Review]:
    """Extract content from an individual review page like https://www.wongnai.com/reviews/xyz"""
    try:
        print(f"DEBUG: Extracting from individual review page: {page.title()}")
        
        # First get the full content to extract username from
        full_content = ""
        content_selectors = [
            "main",
            "[class*=content]",
            "[class*=review]",
            "[class*=text]",
            "article",
            "body"
        ]
        
        for selector in content_selectors:
            content_elem = page.query_selector(selector)
            if content_elem:
                full_content = content_elem.inner_text().strip()
                if len(full_content) > 1000:  # Should be substantial
                    break
        
        # Extract username from the content text using patterns
        user_name = "unknown"
        if full_content:
            # Look for patterns like "KoishiPloy 18 238 1.7k", "JJYY - BKK Street Food Lover 106 1.7k 17.1k"
            import re
            
            # Pattern 1: Name followed by numbers (common Wongnai pattern)
            username_patterns = [
                r'รีวิว ข้าวหมกไก่สยาม สวนสมเด็จฯ \(ศรีสมาน\)\s+([A-Za-z0-9\s\-\.]+?)\s+\d+',
                r'Quality Review\s+([A-Za-z0-9\s\-\.]+?)\s+\d+',
                r'ยืนยันตัวตนแล้ว\s+[^a-zA-Z]*([A-Za-z0-9\s\-\.]+?)\s+\d+',
                # Look for names before numbers patterns
                r'([A-Za-z][A-Za-z0-9\s\-\.]{2,25}?)\s+\d+\s+[\d\.]+k?\s+[\d\.]+k?',
                # Look for names in specific contexts
                r'รีวิว[^a-zA-Z]*([A-Za-z][A-Za-z0-9\s\-\.]{2,25}?)\s+\d',
            ]
            
            for pattern in username_patterns:
                match = re.search(pattern, full_content)
                if match:
                    potential_username = match.group(1).strip()
                    # Filter out restaurant names and common phrases
                    skip_terms = ["ข้าวหมกไก่สยาม", "สวนสมเด็จ", "ศรีสมาน", "Quality", "Review", "รีวิว", "ยืนยัน", "ตัวตน"]
                    if not any(skip in potential_username for skip in skip_terms) and len(potential_username) < 50:
                        user_name = potential_username
                        print(f"DEBUG: Extracted username from content: '{user_name}'")
                        break
            
            # If no pattern match, try to find names manually from the content
            if user_name == "unknown":
                # Look for common Thai/English reviewer names in the content
                lines = full_content.split('\n')
                for line in lines[:20]:  # Check first 20 lines
                    line = line.strip()
                    if re.match(r'^[A-Za-z][A-Za-z0-9\s\-\.]{2,25}$', line):
                        skip_terms = ["Quality Review", "รีวิว", "ข้าว", "สยาม", "สวน", "ศรี", "สมาน"]
                        if not any(skip in line for skip in skip_terms):
                            user_name = line
                            print(f"DEBUG: Found username in line: '{user_name}'")
                            break
        
        # Extract rating
        rating = None
        rating_selectors = [
            "[class*=star]",
            "[class*=rating]", 
            "[class*=score]"
        ]
        
        for selector in rating_selectors:
            rating_elem = page.query_selector(selector)
            if rating_elem:
                rating_text = rating_elem.inner_text().strip()
                # Look for numbers like "4.5", "5/5", etc.
                import re
                rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                        print(f"DEBUG: Found rating: {rating}")
                        break
                    except:
                        continue
        
        # Extract review text - look for main content areas
        review_text = ""
        content_selectors = [
            "main",
            "[class*=content]",
            "[class*=review]",
            "[class*=text]",
            "article",
            "p"
        ]
        
        for selector in content_selectors:
            content_elems = page.query_selector_all(selector)
            if content_elems:
                # Get the element with the most text
                best_elem = None
                max_length = 0
                
                for elem in content_elems:
                    text = elem.inner_text().strip()
                    if len(text) > max_length and len(text) > 50:  # Must be substantial
                        max_length = len(text)
                        best_elem = elem
                
                if best_elem:
                    review_text = best_elem.inner_text().strip()
                    print(f"DEBUG: Found review text ({len(review_text)} chars) with selector '{selector}'")
                    break
        
        # Handle "อ่านต่อ" (read more) links on the individual page
        if "อ่านต่อ" in review_text:
            read_more_link = page.query_selector("a:has-text('อ่านต่อ'), a:has-text('Read more')")
            if read_more_link:
                try:
                    read_more_link.click()
                    page.wait_for_timeout(1000)
                    # Re-extract content after expanding
                    expanded_content = page.query_selector("main, [class*=content], article")
                    if expanded_content:
                        expanded_text = expanded_content.inner_text().strip()
                        if len(expanded_text) > len(review_text):
                            review_text = expanded_text
                            print(f"DEBUG: Expanded text to {len(review_text)} chars")
                except Exception as e:
                    print(f"DEBUG: Failed to expand text: {e}")
        
        # Filter out poor content
        if len(review_text) < 30:
            print(f"DEBUG: Review text too short ({len(review_text)} chars)")
            return None
        
        # Extract review ID from URL
        review_id = review_url.split("/reviews/")[-1].split("?")[0] if "/reviews/" in review_url else "unknown"
        
        return Review(
            restaurant_slug=review_url,
            review_id=review_id,
            user_name=user_name,
            rating=rating,
            review_text=review_text,
            created_at=datetime.now(timezone.utc),
            like_count=None,
            reply_count=None,
            url=review_url,
        )
        
    except Exception as e:
        print(f"DEBUG: Error extracting individual review: {e}")
        return None


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
    # Normalize output path: if user passed a directory or non-csv, coerce to wongnai_reviews.csv in CWD
    p = Path(path)
    if p.is_dir():
        csv_path = p / "wongnai_reviews.csv"
    else:
        if p.suffix.lower() != ".csv":
            csv_path = Path.cwd().parent / "wongnai_reviews.csv"
        else:
            csv_path = p
    header = ["restaurant_slug","review_id","user_name","rating","review_text","created_at","like_count","reply_count","url"]
    mode = "a" if append and csv_path.exists() else "w"
    with open(csv_path, mode, newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if mode == "w":
            w.writerow(header)
        for r in reviews:
            w.writerow(r.to_row())
    print(f"Wrote {len(reviews)} reviews to {csv_path}")


def main():
    args = parse_args()
    existing_ids: set[str] = set()
    if args.skip_existing_csv and Path(args.out).exists():
        try:
            with open(args.out, encoding="utf-8") as f:
                first = True
                for line in f:
                    if first:
                        first = False
                        continue
                    parts = line.rstrip("\n").split(",")
                    if len(parts) > 1:
                        existing_ids.add(parts[1])
            print(f"Loaded {len(existing_ids)} existing review_ids from {args.out}")
        except Exception as e:
            print(f"WARN: could not load existing ids: {e}")

    # Direct single review mode
    if args.review_url:
        reviews = extract_review_page(args.review_url, args.delay)
        if existing_ids:
            reviews = [r for r in reviews if r.review_id not in existing_ids]
        clean = filter_and_trim(reviews, args.since_days, args.limit_per)
        write_output(args.out, clean, args.append, args.raw_json)
        return

    if not args.slugs:
        print("ERROR: either --slugs or --review-url must be provided", file=sys.stderr)
        return
    slugs = load_slugs(args.slugs)
    all_reviews: List[Review] = []
    for slug in slugs:
        url = BASE_URL.format(slug=slug)
        html = fetch_html(url, args.delay)
        if not html:
            print(f"WARN: failed to fetch {slug}")
            continue
        # Shallow extraction (list page)
        reviews = extract_reviews(slug, html)
        # Deep extraction: follow individual review permalinks
        soup = BeautifulSoup(html, "html.parser")
        permalinks = []
        for a in soup.select("a[href*='/reviews/']"):
            href = a.get("href")
            if not href:
                continue
            if href.startswith("/reviews/"):
                full = f"https://www.wongnai.com{href}"
            elif href.startswith("http"):
                full = href
            else:
                full = f"https://www.wongnai.com{href}"
            permalinks.append(full)
        # Deduplicate permalinks
        seen_pl = set()
        deep_reviews: List[Review] = []
        for pl in permalinks:
            if len(deep_reviews) >= args.limit_per:
                break
            rid = pl.rstrip("/\n").split("/")[-1]
            if rid in seen_pl:
                continue
            seen_pl.add(rid)
            if existing_ids and rid in existing_ids:
                continue
            detail = extract_review_page(pl, args.delay)
            if detail:
                deep_reviews.extend(detail)
        if deep_reviews:
            # Merge by review_id (deep overrides shallow)
            merged = {r.review_id: r for r in reviews}
            for dr in deep_reviews:
                merged[dr.review_id] = dr
            reviews = list(merged.values())
        clean = filter_and_trim(reviews, args.since_days, args.limit_per)
        if existing_ids:
            clean = [r for r in clean if r.review_id not in existing_ids]
        for r in clean:
            existing_ids.add(r.review_id)
        all_reviews.extend(clean)
        print(f"{slug}: shallow={len(reviews)} deep_new={len(deep_reviews)} kept={len(clean)} cumulative={len(all_reviews)}")
    write_output(args.out, all_reviews, args.append, args.raw_json)

if __name__ == "__main__":
    main()
