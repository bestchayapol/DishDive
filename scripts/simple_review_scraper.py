#!/usr/bin/env python3
"""
Simple Review Scraper for Wongnai - Step 3 of Strategic Plan

This scraper is optimized for restaurants with ≤8 reviews that don't require pagination.
It extracts all reviews from the first page only, making it faster and less likely to trigger bot detection.

Usage:
    python simple_review_scraper.py --input review_counts_full.jsonl --output simple_reviews.csv --delay 3

Author: AI Assistant
"""

import argparse
import asyncio
import csv
import hashlib
import json
import re
import time
from pathlib import Path
from playwright.async_api import async_playwright
from urllib.parse import urljoin
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleReviewScraper:
    def __init__(self, delay=3):
        self.delay = delay
        self.extracted_reviews = []
        self.seen_reviews = set()  # For duplicate detection
        
    async def extract_individual_review_content(self, page, review_url):
        """Extract full review content from individual review page"""
        try:
            await page.goto(review_url, wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_timeout(2000)  # Wait for dynamic content
            
            # Use comprehensive selectors like the working legacy scraper
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
                content_elems = await page.query_selector_all(selector)
                if content_elems:
                    # Get the element with the most text
                    best_elem = None
                    max_length = 0
                    
                    for elem in content_elems:
                        text = await elem.inner_text()
                        text = text.strip() if text else ""
                        if len(text) > max_length and len(text) > 50:  # Must be substantial
                            max_length = len(text)
                            best_elem = elem
                    
                    if best_elem:
                        review_text = await best_elem.inner_text()
                        review_text = review_text.strip() if review_text else ""
                        logger.info(f"    Found review text ({len(review_text)} chars) with selector '{selector}'")
                        break
            
            # Handle "อ่านต่อ" (read more) links on the individual page
            if "อ่านต่อ" in review_text:
                read_more_link = await page.query_selector("a:has-text('อ่านต่อ'), a:has-text('Read more')")
                if read_more_link:
                    try:
                        full_url = await read_more_link.get_attribute("href")
                        if full_url and "/reviews/" in full_url:
                            if full_url.startswith("/reviews/"):
                                full_url = f"https://www.wongnai.com{full_url}"
                            page2 = await page.context.new_page()
                            await page2.goto(full_url, wait_until='domcontentloaded', timeout=45000)
                            await page2.wait_for_timeout(2000)
                            
                            # Try to get full content from expanded page
                            for selector in content_selectors:
                                full_elems = await page2.query_selector_all(selector)
                                if full_elems:
                                    best_elem = None
                                    max_length = 0
                                    for elem in full_elems:
                                        text = await elem.inner_text()
                                        text = text.strip() if text else ""
                                        if len(text) > max_length and len(text) > len(review_text):
                                            max_length = len(text)
                                            best_elem = elem
                                    
                                    if best_elem:
                                        expanded_text = await best_elem.inner_text()
                                        expanded_text = expanded_text.strip() if expanded_text else ""
                                        if len(expanded_text) > len(review_text):
                                            review_text = expanded_text
                                            logger.info(f"    Expanded review text to {len(review_text)} chars")
                                        break
                            
                            await page2.close()
                    except Exception as e:
                        logger.warning(f"    Failed to expand review: {e}")
            
            # Filter out poor content
            if len(review_text) < 30:
                logger.warning(f"    Review text too short ({len(review_text)} chars)")
                return "No substantial content found"
            
            return review_text
            
        except Exception as e:
            logger.warning(f"Failed to extract from {review_url}: {e}")
            return "Error extracting content"

    def extract_username_from_text(self, text):
        """Extract username from review text using various patterns"""
        if not text:
            return "Unknown"
            
        # Pattern 1: Username at the beginning followed by various indicators
        patterns = [
            r'^([A-Za-z0-9\s\-_\.\'\"]+?)\s*(?:รีวิว|review|commented|posted|wrote)',
            r'^([A-Za-z0-9\s\-_\.\'\"]+?)\s*(?:ได้ทาน|ไปทาน|กิน|ลิ้ม)',
            r'^([A-Za-z0-9\s\-_\.\'\"]+?)\s*(?:บอกว่า|เล่าว่า|พูดว่า)',
            r'^([A-Za-z0-9\s\-_\.\'\"]+?)\s*(?:\:|\-|\–)',
            r'^([A-Za-z0-9\s\-_\.\'\"]+?)\s+(?=.*(?:อร่อย|เด็ด|อร่อยมาก|ไม่อร่อย|บริการ))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.strip(), re.IGNORECASE)
            if match:
                username = match.group(1).strip()
                # Clean up the username
                username = re.sub(r'^(รีวิว|review|by|โดย)\s*', '', username, flags=re.IGNORECASE)
                if len(username) >= 2 and len(username) <= 50:  # Reasonable username length
                    return username
        
        # Fallback: try to find any name-like pattern at the start
        fallback_match = re.match(r'^([A-Za-z0-9\s\-_\.\'\"]{2,30})', text.strip())
        if fallback_match:
            potential_name = fallback_match.group(1).strip()
            # Avoid restaurant names or common phrases
            avoid_words = ['ร้าน', 'restaurant', 'cafe', 'food', 'อาหาร', 'เมนู', 'menu', 'location', 'ที่ตั้ง']
            if not any(word in potential_name.lower() for word in avoid_words):
                return potential_name
        
        return "Anonymous"

    async def scrape_restaurant_reviews(self, browser, restaurant_data):
        """Scrape all reviews from a single restaurant (first page only)"""
        restaurant_url = restaurant_data['restaurant_url']
        restaurant_name = restaurant_data.get('original_data', {}).get('name', 'Unknown')
        
        logger.info(f"Scraping reviews for: {restaurant_name}")
        logger.info(f"URL: {restaurant_url}")
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Add anti-bot detection measures
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        page = await context.new_page()
        
        try:
            # Go to restaurant page
            await page.goto(restaurant_url, wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_timeout(3000)  # Wait for content to load
            
            # Find review links on the listing page using proven selectors
            review_link_selectors = [
                # Direct links to individual reviews (both /reviews/ and reviews/ patterns)
                "a[href*='reviews/']",
                "a[href*='/reviews/']", 
                # More general approaches
                "[href*='reviews/']",
                "[href*='/reviews/']",
                "div[class*=card] a[href*='reviews/']",
                "div[class*=review] a[href*='reviews/']"
            ]
            
            review_links = []
            for selector in review_link_selectors:
                elements = await page.query_selector_all(selector)
                logger.info(f"  Selector '{selector}' found {len(elements)} review links")
                if elements:
                    # Get href attributes
                    for element in elements:
                        href = await element.get_attribute('href')
                        if href and "reviews/" in href:
                            if href.startswith("/"):
                                href = f"https://www.wongnai.com{href}"
                            elif not href.startswith("http"):
                                href = f"https://www.wongnai.com/{href}"
                            if href not in review_links:
                                review_links.append(href)
                    break  # Use first selector that finds links
            
            logger.info(f"Found {len(review_links)} review links")
            
            # Extract content from each review page
            restaurant_reviews = []
            for i, review_url in enumerate(review_links, 1):
                logger.info(f"  Processing review {i}/{len(review_links)}")
                
                # Extract full content from individual review page
                review_text = await self.extract_individual_review_content(page, review_url)
                
                if review_text and len(review_text.strip()) > 10:
                    # Extract username from review text
                    username = self.extract_username_from_text(review_text)
                    
                    # Create review record
                    review_record = {
                        'restaurant_id': restaurant_data.get('original_data', {}).get('id', ''),
                        'restaurant_name': restaurant_name,
                        'restaurant_url': restaurant_url,
                        'review_url': review_url,
                        'username': username,
                        'review_text': review_text,
                        'review_length': len(review_text),
                        'extraction_method': 'individual_page'
                    }
                    
                    # Check for duplicates using username + content hash
                    content_hash = hashlib.md5((username + review_text).encode()).hexdigest()
                    if content_hash not in self.seen_reviews:
                        self.seen_reviews.add(content_hash)
                        restaurant_reviews.append(review_record)
                        logger.info(f"    ✓ Extracted review by {username} ({len(review_text)} chars)")
                    else:
                        logger.info(f"    - Skipped duplicate review by {username}")
                
                # Delay between individual review extractions
                await page.wait_for_timeout(1000)
            
            await context.close()
            return restaurant_reviews
            
        except Exception as e:
            logger.error(f"Error scraping {restaurant_url}: {e}")
            await context.close()
            return []

    async def run_scraping(self, input_file, output_file, max_restaurants=None):
        """Main scraping function for simple strategy restaurants"""
        
        # Load restaurant data and filter for simple strategy only
        restaurants_to_scrape = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    # Only process restaurants marked as 'simple' strategy
                    if data.get('scraping_strategy') == 'simple':
                        restaurants_to_scrape.append(data)
                        if max_restaurants and len(restaurants_to_scrape) >= max_restaurants:
                            break
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed line {line_num}: {e}")
        
        total_simple = len(restaurants_to_scrape)
        logger.info(f"Found {total_simple} restaurants with simple strategy (≤8 reviews)")
        
        if total_simple == 0:
            logger.warning("No restaurants found with simple strategy. Make sure review count analysis is complete.")
            return
        
        # Start scraping
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Visible browser to avoid detection
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-first-run',
                    '--disable-default-apps'
                ]
            )
            
            # Prepare CSV output
            output_path = Path(output_file).parent / Path(output_file).name
            fieldnames = [
                'restaurant_id', 'restaurant_name', 'restaurant_url', 'review_url',
                'username', 'review_text', 'review_length', 'extraction_method'
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for i, restaurant_data in enumerate(restaurants_to_scrape, 1):
                    restaurant_name = restaurant_data.get('original_data', {}).get('name', 'Unknown')
                    review_count = restaurant_data.get('review_count', 0)
                    
                    logger.info(f"\n[{i}/{total_simple}] Processing: {restaurant_name} ({review_count} reviews)")
                    
                    # Scrape reviews for this restaurant
                    reviews = await self.scrape_restaurant_reviews(browser, restaurant_data)
                    
                    # Write reviews to CSV
                    if reviews:
                        for review in reviews:
                            writer.writerow(review)
                        logger.info(f"  → Extracted {len(reviews)} reviews")
                        self.extracted_reviews.extend(reviews)
                    else:
                        logger.info(f"  → No reviews extracted")
                    
                    # Delay between restaurants
                    if i < total_simple:  # Don't delay after the last restaurant
                        logger.info(f"  Waiting {self.delay} seconds before next restaurant...")
                        await asyncio.sleep(self.delay)
            
            await browser.close()
        
        # Final summary
        total_reviews = len(self.extracted_reviews)
        unique_restaurants = len(set(r['restaurant_id'] for r in self.extracted_reviews))
        
        logger.info(f"\n🎉 Simple Strategy Scraping Complete!")
        logger.info(f"Total restaurants processed: {total_simple}")
        logger.info(f"Total reviews extracted: {total_reviews}")
        logger.info(f"Restaurants with reviews: {unique_restaurants}")
        logger.info(f"Average reviews per restaurant: {total_reviews/unique_restaurants if unique_restaurants > 0 else 0:.1f}")
        logger.info(f"Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Simple Wongnai Review Scraper for restaurants with ≤8 reviews')
    parser.add_argument('--input', required=True, help='Input JSONL file with review count analysis')
    parser.add_argument('--output', required=True, help='Output CSV file for extracted reviews')
    parser.add_argument('--delay', type=int, default=3, help='Delay between restaurants in seconds (default: 3)')
    parser.add_argument('--limit', type=int, help='Limit number of restaurants to process (for testing)')
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run scraper
    scraper = SimpleReviewScraper(delay=args.delay)
    asyncio.run(scraper.run_scraping(args.input, args.output, args.limit))


if __name__ == "__main__":
    main()