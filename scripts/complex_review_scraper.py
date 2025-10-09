#!/usr/bin/env python3
"""
Complex Review Scraper with Adaptive Bot Detection - Step 4 of Strategic Plan

This scraper implements a hybrid approach for restaurants with >8 reviews:
1. Tests bot detection patterns and learns optimal delays
2. Processes restaurants in small batches with adaptive timing
3. Provides manual intervention mode when automation fails
4. Learns from successful patterns to optimize future runs

Usage:
    # Test mode: Learn bot detection patterns
    python complex_review_scraper.py --input review_counts_full.jsonl --mode test --batch-size 3

    # Auto mode: Process restaurants with learned patterns
    python complex_review_scraper.py --input review_counts_full.jsonl --mode auto --batch-size 5

    # Manual mode: User assists with pagination
    python complex_review_scraper.py --input review_counts_full.jsonl --mode manual --batch-size 1

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
from datetime import datetime, timedelta
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BotDetectionManager:
    def __init__(self):
        self.detection_log = []
        self.successful_delays = []
        self.failed_attempts = []
        self.learned_patterns = {}
    
    def log_attempt(self, delay_used, pages_loaded, success, detection_triggered):
        """Log pagination attempt results"""
        attempt = {
            'timestamp': datetime.now(),
            'delay_used': delay_used,
            'pages_loaded': pages_loaded,
            'success': success,
            'detection_triggered': detection_triggered
        }
        self.detection_log.append(attempt)
        
        if success and pages_loaded > 1:
            self.successful_delays.append(delay_used)
        elif detection_triggered:
            self.failed_attempts.append(delay_used)
    
    def get_recommended_delay(self):
        """Get recommended delay based on learning"""
        if self.successful_delays:
            # Use average of successful delays + safety margin
            avg_success = sum(self.successful_delays) / len(self.successful_delays)
            return max(avg_success * 1.5, 10)  # At least 10 seconds
        elif self.failed_attempts:
            # If we have failures, be more conservative
            max_failed = max(self.failed_attempts) if self.failed_attempts else 5
            return max_failed * 2
        else:
            # Default starting delay
            return 8
    
    def is_detection_likely(self):
        """Predict if bot detection is likely based on recent attempts"""
        recent_attempts = [a for a in self.detection_log if 
                          datetime.now() - a['timestamp'] < timedelta(minutes=30)]
        
        if len(recent_attempts) >= 3:
            recent_failures = sum(1 for a in recent_attempts if a['detection_triggered'])
            failure_rate = recent_failures / len(recent_attempts)
            return failure_rate > 0.5
        
        return False

class ComplexReviewScraper:
    def __init__(self, mode='auto', batch_size=5):
        self.mode = mode  # 'test', 'auto', 'manual'
        self.batch_size = batch_size
        self.bot_manager = BotDetectionManager()
        self.extracted_reviews = []
        self.seen_reviews = set()
        self.session_stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'manual_interventions': 0
        }

    async def test_pagination_pattern(self, page, restaurant_url):
        """Test pagination with different delay patterns to learn bot detection"""
        logger.info("🧪 Testing pagination patterns...")
        
        test_delays = [5, 8, 12, 15, 20]
        results = []
        
        for delay in test_delays:
            try:
                await page.goto(restaurant_url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Try to click "view more" button
                view_more_selectors = [
                    '//button[contains(text(), "ดูรีวิวเพิ่มเติม")]',
                    '//button[contains(text(), "view more")]',
                    '//a[contains(text(), "ดูรีวิวเพิ่มเติม")]',
                    '.load-more-reviews',
                    '.view-more-button'
                ]
                
                pages_loaded = 1
                detection_triggered = False
                
                for attempt in range(3):  # Try to load 3 more pages
                    button_clicked = False
                    
                    for selector in view_more_selectors:
                        try:
                            if selector.startswith('//'):
                                button = await page.wait_for_selector(selector, timeout=5000)
                            else:
                                button = await page.wait_for_selector(selector, timeout=5000)
                            
                            if button:
                                await button.click()
                                button_clicked = True
                                break
                        except:
                            continue
                    
                    if not button_clicked:
                        break
                    
                    # Wait with the test delay
                    await page.wait_for_timeout(delay * 1000)
                    
                    # Check if new content loaded
                    new_reviews = await page.query_selector_all('a[href*="/review"]')
                    if len(new_reviews) > pages_loaded * 8:  # More reviews appeared
                        pages_loaded += 1
                        logger.info(f"  ✓ Page {pages_loaded} loaded with {delay}s delay")
                    else:
                        # Possible bot detection
                        detection_triggered = True
                        logger.warning(f"  ⚠️ Bot detection likely with {delay}s delay")
                        break
                
                success = pages_loaded > 1 and not detection_triggered
                self.bot_manager.log_attempt(delay, pages_loaded, success, detection_triggered)
                
                results.append({
                    'delay': delay,
                    'pages_loaded': pages_loaded,
                    'success': success,
                    'detection_triggered': detection_triggered
                })
                
                logger.info(f"  Delay {delay}s: {pages_loaded} pages, Success: {success}")
                
                # Wait longer between tests
                await page.wait_for_timeout(random.randint(10000, 15000))
                
            except Exception as e:
                logger.error(f"Test failed for delay {delay}s: {e}")
        
        # Analyze results
        successful_delays = [r['delay'] for r in results if r['success']]
        if successful_delays:
            recommended = min(successful_delays)  # Use the fastest successful delay
            logger.info(f"🎯 Recommended delay: {recommended}s (from successful: {successful_delays})")
        else:
            recommended = 20  # Conservative fallback
            logger.warning(f"⚠️ No successful patterns found, using conservative {recommended}s")
        
        return recommended, results

    async def scrape_with_pagination(self, page, restaurant_data, learned_delay=None):
        """Scrape restaurant with adaptive pagination"""
        restaurant_url = restaurant_data['restaurant_url']
        restaurant_name = restaurant_data.get('original_data', {}).get('name', 'Unknown')
        review_count = restaurant_data.get('review_count', 0)
        
        logger.info(f"🔄 Processing: {restaurant_name} ({review_count} reviews)")
        
        try:
            # Use same navigation approach as working legacy script
            await page.goto(restaurant_url, wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_timeout(3000)
            
            # Get initial review links
            all_review_links = []
            initial_links = await self.get_review_links(page)
            all_review_links.extend(initial_links)
            
            logger.info(f"  Initial page: {len(initial_links)} review links")
            
            # Determine delay strategy
            if self.mode == 'test':
                delay, test_results = await self.test_pagination_pattern(page, restaurant_url)
                return [], test_results  # Return test results instead of reviews
            
            elif self.mode == 'manual':
                # Manual pagination mode
                pages_loaded = await self.manual_pagination(page)
                if pages_loaded > 1:
                    final_links = await self.get_review_links(page)
                    all_review_links = final_links  # Use final state
                    logger.info(f"  Manual pagination: {len(all_review_links)} total links from {pages_loaded} pages")
            
            else:  # auto mode
                # Automatic pagination with learned delays
                if learned_delay:
                    delay = learned_delay
                elif self.bot_manager.successful_delays:
                    delay = self.bot_manager.get_recommended_delay()
                else:
                    delay = 10  # Conservative start
                
                logger.info(f"  Using {delay}s delay for pagination")
                
                # Try automatic pagination
                pages_loaded = await self.auto_pagination(page, delay)
                if pages_loaded > 1:
                    final_links = await self.get_review_links(page)
                    all_review_links = final_links
                    logger.info(f"  Auto pagination: {len(all_review_links)} total links from {pages_loaded} pages")
            
            # Extract reviews from all collected links
            restaurant_reviews = []
            for i, review_url in enumerate(all_review_links, 1):
                if i > 50:  # Limit to prevent excessive processing
                    logger.info(f"  Limiting to first 50 reviews")
                    break
                
                logger.info(f"    Processing review {i}/{min(len(all_review_links), 50)}")
                
                # Extract review content (reuse from simple scraper)
                review_text = await self.extract_individual_review_content(page, review_url)
                
                if review_text and len(review_text.strip()) > 10:
                    username = self.extract_username_from_text(review_text)
                    
                    review_record = {
                        'restaurant_id': restaurant_data.get('original_data', {}).get('id', ''),
                        'restaurant_name': restaurant_name,
                        'restaurant_url': restaurant_url,
                        'review_url': review_url,
                        'username': username,
                        'review_text': review_text,
                        'review_length': len(review_text),
                        'extraction_method': 'complex_pagination'
                    }
                    
                    # Duplicate detection
                    content_hash = hashlib.md5((username + review_text).encode()).hexdigest()
                    if content_hash not in self.seen_reviews:
                        self.seen_reviews.add(content_hash)
                        restaurant_reviews.append(review_record)
                
                await page.wait_for_timeout(1000)  # Brief delay between reviews
            
            return restaurant_reviews, None
            
        except Exception as e:
            logger.error(f"Error processing {restaurant_name}: {e}")
            return [], None

    async def manual_pagination(self, page):
        """Manual pagination mode - wait for user to click buttons"""
        pages_loaded = 1
        
        logger.info("🖱️  MANUAL MODE: Please click 'view more reviews' buttons when ready")
        logger.info("    Type 'done' and press Enter when you've loaded all pages you want")
        logger.info("    Type 'skip' and press Enter to skip this restaurant")
        
        while True:
            try:
                # Non-blocking input check
                user_input = input("    Ready for next page? (Enter='next', 'done'=finish, 'skip'=abort): ").strip().lower()
                
                if user_input == 'done':
                    break
                elif user_input == 'skip':
                    logger.info("  Skipping restaurant by user request")
                    return 0
                else:
                    # User pressed Enter or typed something else - assume they clicked
                    await page.wait_for_timeout(2000)  # Let content load
                    pages_loaded += 1
                    logger.info(f"  Page {pages_loaded} loaded")
                    self.session_stats['manual_interventions'] += 1
                    
            except KeyboardInterrupt:
                logger.info("  Manual mode interrupted")
                break
        
        return pages_loaded

    async def auto_pagination(self, page, delay):
        """Automatic pagination with bot detection awareness"""
        pages_loaded = 1
        max_pages = 10  # Safety limit
        
        # Use proven selectors from working legacy scraper
        view_more_selectors = [
            "button:has-text('เพิ่มเติม')",
            "button:has-text('ดูรีวิวเพิ่มเติม')",
            "button:has-text('view more')",
            "a button",
            "[class*=more] button"
        ]
        
        for page_num in range(2, max_pages + 1):
            button_found = False
            
            # Try to find and click "view more" button
            load_more_button = None
            for selector in view_more_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button and await button.is_visible():
                        load_more_button = button
                        logger.info(f"    Found load more button: {selector}")
                        break
                except:
                    continue
            
            if load_more_button:
                try:
                    initial_reviews = await page.query_selector_all('a[href*="review"]')
                    initial_count = len(initial_reviews)
                    
                    logger.info(f"    Clicking load more button for page {page_num}")
                    await load_more_button.click()
                    button_found = True
                    
                    # Wait with learned delay
                    await page.wait_for_timeout(delay * 1000)
                    
                    # Check if new content appeared
                    new_reviews = await page.query_selector_all('a[href*="review"]')
                    new_count = len(new_reviews)
                    
                    if new_count > initial_count:
                        pages_loaded = page_num
                        logger.info(f"    ✓ Page {page_num} loaded ({new_count} total reviews)")
                        
                        # Log successful pagination
                        self.bot_manager.log_attempt(delay, page_num, True, False)
                    else:
                        # Possible bot detection
                        logger.warning(f"    ⚠️ No new content after click - possible bot detection")
                        self.bot_manager.log_attempt(delay, page_num, False, True)
                        return pages_loaded  # Stop trying
                        
                except Exception as e:
                    logger.error(f"    Failed to click load more: {e}")
                    break
            else:
                logger.info(f"    No load more button found, stopping at page {page_num}")
                break
        
        return pages_loaded

    async def get_review_links(self, page):
        """Extract all review links from current page state"""
        # Use proven selectors from working legacy scraper
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
        
        logger.info(f"  Found {len(review_links)} unique review links total")
        return review_links

    # Reuse methods from simple scraper
    async def extract_individual_review_content(self, page, review_url):
        """Extract full review content from individual review page"""
        try:
            await page.goto(review_url, wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_timeout(2000)
            
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
        
        patterns = [
            r'^([A-Za-z0-9\s\-_\.\'\"]+?)\s*(?:รีวิว|review|commented|posted|wrote)',
            r'^([A-Za-z0-9\s\-_\.\'\"]+?)\s*(?:ได้ทาน|ไปทาน|กิน|ลิ้ม)',
            r'^([A-Za-z0-9\s\-_\.\'\"]+?)\s*(?:บอกว่า|เล่าว่า|พูดว่า)',
            r'^([A-Za-z0-9\s\-_\.\'\"]+?)\s*(?:\:|\-|\–)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.strip(), re.IGNORECASE)
            if match:
                username = match.group(1).strip()
                if len(username) >= 2 and len(username) <= 50:
                    return username
        
        return "Anonymous"

    async def run_complex_scraping(self, input_file, output_file, max_restaurants=None, start_index=0, end_index=None):
        """Main function for complex strategy scraping"""
        
        # Load restaurants marked as 'complex' strategy
        restaurants_to_scrape = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get('scraping_strategy') == 'complex':
                        restaurants_to_scrape.append(data)
                except json.JSONDecodeError:
                    continue
        
        total_complex = len(restaurants_to_scrape)
        logger.info(f"Found {total_complex} restaurants with complex strategy (>8 reviews)")
        
        if total_complex == 0:
            logger.warning("No restaurants found with complex strategy")
            return
        
        # Apply range selection
        if end_index is None:
            end_index = total_complex
        
        # Apply start/end slicing
        restaurants_to_scrape = restaurants_to_scrape[start_index:end_index]
        
        # Apply max_restaurants limit after slicing
        if max_restaurants:
            restaurants_to_scrape = restaurants_to_scrape[:max_restaurants]
        
        actual_count = len(restaurants_to_scrape)
        logger.info(f"Processing restaurants {start_index} to {start_index + actual_count - 1} ({actual_count} total)")
        
        if actual_count == 0:
            logger.warning("No restaurants to process in the specified range")
            return
        
        # Process in batches
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-first-run',
                    '--disable-default-apps'
                ]
            )
            
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
            
            # Setup CSV output
            output_path = Path(output_file)
            fieldnames = [
                'restaurant_id', 'restaurant_name', 'restaurant_url', 'review_url',
                'username', 'review_text', 'review_length', 'extraction_method'
            ]
            
            # Check if file exists to determine if we need to write header
            file_exists = output_path.exists()
            
            with open(output_path, 'a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                
                learned_delay = None
                
                # Process restaurants in batches
                for batch_start in range(0, actual_count, self.batch_size):
                    batch_end = min(batch_start + self.batch_size, total_complex)
                    batch_restaurants = restaurants_to_scrape[batch_start:batch_end]
                    
                    logger.info(f"\n📦 Processing batch {batch_start//self.batch_size + 1}: restaurants {batch_start+1}-{batch_end}")
                    
                    for i, restaurant_data in enumerate(batch_restaurants):
                        restaurant_name = restaurant_data.get('original_data', {}).get('name', 'Unknown')
                        
                        try:
                            reviews, test_results = await self.scrape_with_pagination(page, restaurant_data, learned_delay)
                            
                            if self.mode == 'test' and test_results:
                                logger.info(f"  Test results for {restaurant_name}: {test_results}")
                                # In test mode, learn from results
                                successful_results = [r for r in test_results if r['success']]
                                if successful_results:
                                    learned_delay = min(r['delay'] for r in successful_results)
                                    logger.info(f"  📚 Learned optimal delay: {learned_delay}s")
                            else:
                                # Normal processing
                                if reviews:
                                    for review in reviews:
                                        writer.writerow(review)
                                    logger.info(f"  ✅ Extracted {len(reviews)} reviews")
                                    self.session_stats['successful'] += 1
                                else:
                                    logger.info(f"  ❌ No reviews extracted")
                                    self.session_stats['failed'] += 1
                                
                                self.extracted_reviews.extend(reviews)
                            
                            self.session_stats['processed'] += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to process {restaurant_name}: {e}")
                            self.session_stats['failed'] += 1
                        
                        # Delay between restaurants in batch
                        if i < len(batch_restaurants) - 1:
                            delay = random.randint(5, 10)
                            await asyncio.sleep(delay)
                    
                    # Longer delay between batches
                    if batch_end < total_complex:
                        batch_delay = random.randint(30, 60)  # 30-60 seconds between batches
                        logger.info(f"  💤 Batch complete. Waiting {batch_delay}s before next batch...")
                        await asyncio.sleep(batch_delay)
            
            await browser.close()
        
        # Final statistics
        logger.info(f"\n🎯 Complex Strategy Session Complete!")
        logger.info(f"Restaurants processed: {self.session_stats['processed']}")
        logger.info(f"Successful extractions: {self.session_stats['successful']}")
        logger.info(f"Failed extractions: {self.session_stats['failed']}")
        logger.info(f"Manual interventions: {self.session_stats['manual_interventions']}")
        logger.info(f"Total reviews extracted: {len(self.extracted_reviews)}")
        logger.info(f"Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Complex Wongnai Review Scraper for restaurants with >8 reviews')
    parser.add_argument('--input', default='../outputs/review_counts_parsed.jsonl', help='Input JSONL file with review count analysis')
    parser.add_argument('--output', default='../outputs/complex_reviews.csv', help='Output CSV file for extracted reviews')
    parser.add_argument('--mode', choices=['test', 'auto', 'manual'], default='auto',
                       help='Scraping mode: test=learn patterns, auto=automated, manual=user assists')
    parser.add_argument('--batch-size', type=int, default=5, help='Number of restaurants per batch')
    parser.add_argument('--limit', type=int, help='Limit number of restaurants to process')
    parser.add_argument('--start', type=int, default=0, help='Start index (0-based) for processing restaurants')
    parser.add_argument('--end', type=int, help='End index (0-based, exclusive) for processing restaurants')
    
    args = parser.parse_args()
    
    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run scraper
    scraper = ComplexReviewScraper(mode=args.mode, batch_size=args.batch_size)
    asyncio.run(scraper.run_complex_scraping(args.input, args.output, args.limit, args.start, args.end))


if __name__ == "__main__":
    main()