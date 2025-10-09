#!/usr/bin/env python
"""
Review Count Detector for Wongnai Restaurants

This script analyzes restaurants to detect how many reviews each has,
allowing us to apply different scraping strategies based on review volume.

Usage:
    python review_count_detector.py --input ../outputs/found_slugs.jsonl --output ../outputs/review_counts.jsonl

Strategy:
- Restaurants with ≤8 reviews: Use simple scraping (no pagination needed)  
- Restaurants with >8 reviews: Use complex scraping with backoff strategies
"""

import json
import argparse
import time
import random
from pathlib import Path
from playwright.sync_api import sync_playwright
from typing import Dict, List, Optional
import re

def detect_review_count(page, restaurant_url: str) -> Dict:
    """
    Detect the number of reviews for a restaurant without extracting content.
    Returns dict with restaurant info and review count.
    """
    try:
        print(f"Analyzing: {restaurant_url}")
        page.goto(restaurant_url)
        page.wait_for_timeout(2000)
        
        restaurant_name = page.title()
        
        # Strategy 1: Look for review count in page elements
        review_count = 0
        
        # Try multiple selectors to find review count indicators
        count_selectors = [
            # Look for text like "129 รีวิว" or "129 reviews"
            "text=/\\d+\\s*รีวิว/",
            "text=/\\d+\\s*reviews/i", 
            "text=/\\d+\\s*เรตติ้ง/",
            # Look in common UI elements
            "[class*=review] [class*=count]",
            "[class*=rating] [class*=count]", 
            "[data-testid*=review]",
            # Check breadcrumbs or headers
            "h1, h2, h3",
            "[class*=header]"
        ]
        
        for selector in count_selectors:
            try:
                elements = page.query_selector_all(selector)
                for element in elements:
                    text = element.inner_text().strip()
                    # Extract numbers from text like "129 รีวิว" or "(129 รีวิว)"
                    numbers = re.findall(r'(\\d+)\\s*(?:รีวิว|reviews|เรตติ้ง)', text, re.IGNORECASE)
                    if numbers:
                        review_count = max(review_count, int(numbers[0]))
            except:
                continue
                
        # Strategy 2: Count actual review links as fallback
        if review_count == 0:
            review_links = page.query_selector_all("a[href*='reviews/']")
            visible_reviews = len([link for link in review_links if link.is_visible()])
            review_count = visible_reviews
            
        # Strategy 3: Look for pagination indicators
        has_pagination = False
        pagination_selectors = [
            "button:has-text('เพิ่มเติม')",
            "button:has-text('ดูเพิ่มเติม')", 
            "button:has-text('view more')",
            "[class*=more]",
            "[class*=load]"
        ]
        
        for selector in pagination_selectors:
            try:
                button = page.query_selector(selector)
                if button and button.is_visible():
                    has_pagination = True
                    break
            except:
                continue
                
        # If we see pagination, assume more than what we counted
        if has_pagination and review_count <= 8:
            review_count = max(review_count, 15)  # Conservative estimate
            
        return {
            'restaurant_url': restaurant_url,
            'restaurant_name': restaurant_name,
            'review_count': review_count,
            'has_pagination': has_pagination,
            'scraping_strategy': 'simple' if review_count <= 8 else 'complex'
        }
        
    except Exception as e:
        print(f"Error analyzing {restaurant_url}: {e}")
        return {
            'restaurant_url': restaurant_url,
            'restaurant_name': 'ERROR',
            'review_count': 0,
            'has_pagination': False,
            'scraping_strategy': 'simple',
            'error': str(e)
        }

def main():
    parser = argparse.ArgumentParser(description='Detect review counts for Wongnai restaurants')
    parser.add_argument('--input', required=True, help='Input JSONL file with restaurant slugs')
    parser.add_argument('--output', required=True, help='Output JSONL file with review counts')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests in seconds')
    parser.add_argument('--limit', type=int, help='Limit number of restaurants to analyze')
    
    args = parser.parse_args()
    
    # Read input slugs
    restaurants = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            restaurants.append(data)
    
    if args.limit:
        restaurants = restaurants[:args.limit]
        
    print(f"Analyzing {len(restaurants)} restaurants...")
    
    # Setup browser
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # Run in background for speed
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--no-first-run'
            ]
        )
        page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36')
        
        results = []
        for i, restaurant in enumerate(restaurants, 1):
            slug = restaurant['slug']
            restaurant_url = f"https://www.wongnai.com/restaurants/{slug}"
            
            print(f"[{i}/{len(restaurants)}] Analyzing {restaurant['name']}")
            
            result = detect_review_count(page, restaurant_url)
            result['original_data'] = restaurant
            results.append(result)
            
            # Write results incrementally
            with open(args.output, 'w', encoding='utf-8') as f:
                for r in results:
                    f.write(json.dumps(r, ensure_ascii=False) + '\\n')
            
            # Polite delay
            time.sleep(args.delay + random.uniform(0, args.delay * 0.3))
            
        browser.close()
    
    # Summary statistics
    simple_count = sum(1 for r in results if r.get('scraping_strategy') == 'simple')
    complex_count = sum(1 for r in results if r.get('scraping_strategy') == 'complex')
    
    print(f"\\n=== ANALYSIS COMPLETE ===")
    print(f"Total restaurants: {len(results)}")
    print(f"Simple strategy (≤8 reviews): {simple_count}")
    print(f"Complex strategy (>8 reviews): {complex_count}")
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()