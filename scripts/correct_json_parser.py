#!/usr/bin/env python3
"""
Correct JSON parser for the review_counts_full.jsonl file with escaped newlines
"""

import json
import urllib.parse
import os

def parse_review_counts_file():
    """Parse the malformed JSONL file with escaped newlines."""
    file_path = r"c:\Users\famee\OneDrive\Documents\GitHub\DishDive\outputs\review_counts_full.jsonl"
    
    # Read the entire file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Replace escaped newlines with actual newlines
    content = content.replace('\\n', '\n')
    
    # Split using the pattern: }}\n{"restaurant_url"
    parts = content.split('}}\n{"restaurant_url"')
    
    parsed_restaurants = []
    
    for i, part in enumerate(parts):
        try:
            if i == 0:
                # First part is complete JSON
                json_str = part
            else:
                # Other parts need the opening brace added back
                json_str = '{"restaurant_url"' + part
            
            # Make sure it ends with closing braces
            if not json_str.endswith('}}'):
                json_str += '}}'
                
            # Parse the JSON
            restaurant_data = json.loads(json_str)
            
            # Decode URL-encoded Thai text in restaurant names (if needed)
            if 'restaurant_name' in restaurant_data:
                # Only decode if it contains URL encoding
                if '%' in restaurant_data['restaurant_name']:
                    restaurant_data['restaurant_name'] = urllib.parse.unquote(restaurant_data['restaurant_name'])
            
            parsed_restaurants.append(restaurant_data)
            
        except json.JSONDecodeError as e:
            print(f"Error parsing part {i}: {e}")
            print(f"Problematic JSON (first 200 chars): {json_str[:200]}...")
            continue
    
    print(f"Successfully parsed {len(parsed_restaurants)} restaurants")
    
    # Analyze distribution
    simple_count = sum(1 for r in parsed_restaurants if r.get('scraping_strategy') == 'simple')
    complex_count = sum(1 for r in parsed_restaurants if r.get('scraping_strategy') == 'complex')
    
    print(f"\nDistribution Analysis:")
    print(f"Simple strategy (≤8 reviews): {simple_count} restaurants")
    print(f"Complex strategy (>8 reviews): {complex_count} restaurants")
    print(f"Total: {len(parsed_restaurants)} restaurants")
    
    # Save to proper JSONL format
    output_file = r"c:\Users\famee\OneDrive\Documents\GitHub\DishDive\outputs\review_counts_parsed.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for restaurant in parsed_restaurants:
            f.write(json.dumps(restaurant, ensure_ascii=False) + '\n')
    
    print(f"\nParsed data saved to: {output_file}")
    
    # Show some examples
    print(f"\nSample restaurant data:")
    for i, restaurant in enumerate(parsed_restaurants[:3]):
        print(f"\n{i+1}. {restaurant.get('restaurant_name', 'Unknown')}")
        print(f"   Reviews: {restaurant.get('review_count', 0)}")
        print(f"   Strategy: {restaurant.get('scraping_strategy', 'unknown')}")
        print(f"   URL: {restaurant.get('restaurant_url', 'N/A')[:50]}...")
    
    return parsed_restaurants

if __name__ == "__main__":
    restaurants = parse_review_counts_file()