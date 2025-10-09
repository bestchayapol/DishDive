#!/usr/bin/env python3
"""
Bot Detection Tester for Wongnai

This script tests Wongnai's bot detection behavior by making controlled requests
to understand detection triggers, cooldown periods, and backoff strategies.
"""

import asyncio
import random
import time
from datetime import datetime
from playwright.async_api import async_playwright
import json
import csv
import requests

class BotDetectionTester:
    def __init__(self):
        self.results = []
        self.detection_triggered = False
        self.test_urls = [
            "https://www.wongnai.com/restaurants/1522952FC",  # Complex restaurant (18 reviews)
            "https://www.wongnai.com/restaurants/1817617XR",  # Simple restaurant (7 reviews)
            "https://www.wongnai.com/restaurants/378679Yr-east-view",  # Simple restaurant (5 reviews)
        ]

    async def test_basic_access_pattern(self, page):
        """Test basic access patterns to understand normal vs suspicious behavior"""
        print("🧪 Testing basic access patterns...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Accept-Language": "th,en-US;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        for i, url in enumerate(self.test_urls):
            start_time = time.time()
            try:
                print(f"  Request {i+1}: {url}")
                # Use requests to prefetch cookies (imitate legacy script)
                try:
                    resp = requests.get(url, headers=headers, timeout=15)
                except Exception:
                    resp = None
                # Navigate to page with Playwright
                response = await page.goto(url, wait_until='domcontentloaded', timeout=45000)
                load_time = time.time() - start_time
                # Check if page loaded successfully
                status_code = response.status if response else None
                page_content = await page.content()
                # Improved CAPTCHA detection: check for visible CAPTCHA elements
                captcha_present = False
                try:
                    captcha_present = bool(await page.query_selector('[data-testid="captcha"], .captcha, #captcha, iframe[src*="captcha"], form[action*="captcha"]'))
                except Exception:
                    pass
                # Also check for actual visible overlays
                overlays = await page.query_selector_all('[style*="z-index"]')
                for overlay in overlays:
                    style = await overlay.get_attribute('style')
                    if style and 'captcha' in style:
                        captcha_present = True
                        break
                # Bot indicators
                bot_indicators = {
                    'cloudflare_challenge': 'Checking your browser' in page_content,
                    'access_denied': 'Access Denied' in page_content or 'Forbidden' in page_content,
                    'captcha_present': captcha_present,
                    'rate_limit': 'rate limit' in page_content.lower() or 'too many requests' in page_content.lower(),
                    'suspicious_activity': 'suspicious activity' in page_content.lower()
                }
                # Check if reviews are visible (normal access)
                reviews_visible = False
                try:
                    reviews_section = await page.query_selector("section[aria-label='รีวิว'] div[data-testid='feed-list']")
                    reviews_visible = bool(reviews_section)
                except:
                    pass
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'request_number': i + 1,
                    'url': url,
                    'status_code': status_code,
                    'load_time': round(load_time, 2),
                    'reviews_visible': reviews_visible,
                    **bot_indicators
                }
                self.results.append(result)
                # Print immediate feedback
                if any(bot_indicators.values()):
                    print(f"    ⚠️  Bot detection indicators found: {[k for k, v in bot_indicators.items() if v]}")
                    self.detection_triggered = True
                elif not reviews_visible:
                    print(f"    ⚠️  Reviews not visible (possible soft blocking)")
                else:
                    print(f"    ✅ Normal access (load time: {load_time:.2f}s)")
                # Random delay between requests (2-8 seconds)
                if i < len(self.test_urls) - 1:
                    delay = random.uniform(2, 8)
                    print(f"    ⏱️  Waiting {delay:.1f}s before next request...")
                    await asyncio.sleep(delay)
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                self.results.append({
                    'timestamp': datetime.now().isoformat(),
                    'request_number': i + 1,
                    'url': url,
                    'error': str(e),
                    'load_time': round(time.time() - start_time, 2)
                })

    async def test_rapid_requests(self, page):
        """Test rapid requests to trigger detection"""
        print("\n🚀 Testing rapid request pattern...")
        
        url = self.test_urls[0]  # Use first URL for rapid testing
        
        for i in range(5):  # 5 rapid requests
            start_time = time.time()
            
            try:
                print(f"  Rapid request {i+1}: {url}")
                response = await page.goto(url, wait_until='networkidle', timeout=15000)
                load_time = time.time() - start_time
                
                # Quick detection check
                page_content = await page.content()
                detected = any([
                    'Checking your browser' in page_content,
                    'Access Denied' in page_content,
                    'captcha' in page_content.lower(),
                    'rate limit' in page_content.lower()
                ])
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'test_type': 'rapid_request',
                    'request_number': i + 1,
                    'url': url,
                    'status_code': response.status,
                    'load_time': round(load_time, 2),
                    'bot_detected': detected
                }
                
                self.results.append(result)
                
                if detected:
                    print(f"    ⚠️  Bot detection triggered on request {i+1}")
                    self.detection_triggered = True
                    break
                else:
                    print(f"    ✅ Request {i+1} successful ({load_time:.2f}s)")
                
                # Very short delay (0.5-1.5 seconds) for rapid testing
                if i < 4:
                    delay = random.uniform(0.5, 1.5)
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                print(f"    ❌ Rapid request {i+1} failed: {str(e)}")
                break

    async def test_cooldown_period(self, page):
        """If detection was triggered, test cooldown periods"""
        if not self.detection_triggered:
            print("\n❌ No bot detection triggered, skipping cooldown test")
            return
            
        print("\n⏰ Testing cooldown periods...")
        
        # Test longer cooldowns: 30s, 1m, 2m, 5m, 10m, 15m, 20m, 30m
        cooldown_tests = [30, 60, 120, 300, 600, 900, 1200, 1800]  # seconds
        url = self.test_urls[0]
        
        for cooldown in cooldown_tests:
            print(f"  Waiting {cooldown}s cooldown period...")
            await asyncio.sleep(cooldown)
            
            try:
                start_time = time.time()
                response = await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                load_time = time.time() - start_time
                
                page_content = await page.content()
                still_detected = any([
                    'Checking your browser' in page_content,
                    'Access Denied' in page_content,
                    'captcha' in page_content.lower()
                ])
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'test_type': 'cooldown_test',
                    'cooldown_seconds': cooldown,
                    'url': url,
                    'status_code': response.status,
                    'load_time': round(load_time, 2),
                    'still_detected': still_detected
                }
                
                self.results.append(result)
                
                if not still_detected:
                    print(f"    ✅ Cooldown successful after {cooldown}s")
                    break
                else:
                    print(f"    ⚠️  Still detected after {cooldown}s")
                    
            except Exception as e:
                print(f"    ❌ Cooldown test failed: {str(e)}")

    def save_results(self):
        """Save test results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Save as JSON
        json_file = f"../outputs/bot_detection_test_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'total_requests': len(self.results),
                    'detection_triggered': self.detection_triggered,
                    'test_timestamp': timestamp
                },
                'results': self.results
            }, f, indent=2, ensure_ascii=False)
        # Save as CSV for easy analysis
        csv_file = f"../outputs/bot_detection_test_{timestamp}.csv"
        if self.results:
            # Dynamically get all keys
            all_keys = set()
            for r in self.results:
                all_keys.update(r.keys())
            fieldnames = list(all_keys)
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
        print(f"\n📊 Results saved:")
        print(f"  JSON: {json_file}")
        print(f"  CSV: {csv_file}")

    async def run_tests(self):
        """Run all bot detection tests"""
        print("🔍 Starting Wongnai Bot Detection Tests")
        print("=" * 50)
        
        async with async_playwright() as p:
            # Use visible browser to see what's happening
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # Test 1: Basic access patterns
                await self.test_basic_access_pattern(page)
                
                # Test 2: Rapid requests (if no detection yet)
                if not self.detection_triggered:
                    await self.test_rapid_requests(page)
                
                # Test 3: Cooldown periods (if detection was triggered)
                await self.test_cooldown_period(page)
                
            finally:
                await browser.close()
        
        # Save and summarize results
        self.save_results()
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("🎯 BOT DETECTION TEST SUMMARY")
        print("=" * 50)
        
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r.get('status_code') == 200 and not r.get('bot_detected')])
        
        print(f"Total requests made: {total_requests}")
        print(f"Successful requests: {successful_requests}")
        print(f"Bot detection triggered: {'Yes' if self.detection_triggered else 'No'}")
        
        if self.results:
            avg_load_time = sum(r.get('load_time', 0) for r in self.results) / len(self.results)
            print(f"Average load time: {avg_load_time:.2f}s")
        
        print("\nRecommendations based on test results:")
        if not self.detection_triggered:
            print("✅ No immediate bot detection - can proceed with moderate scraping")
            print("🕒 Recommended delay: 3-8 seconds between requests")
        else:
            print("⚠️  Bot detection active - need careful approach")
            print("🕒 Recommended delay: 60+ seconds between requests")
            print("🔄 Consider rotating user agents and session management")

if __name__ == "__main__":
    tester = BotDetectionTester()
    asyncio.run(tester.run_tests())