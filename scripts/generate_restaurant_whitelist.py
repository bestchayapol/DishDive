#!/usr/bin/env python3
"""Extract restaurant names from the parsed JSON file and create a whitelist for Go backend."""

import json
import os
from pathlib import Path

def extract_restaurant_names(jsonl_file_path):
    """Extract unique restaurant names from the JSONL file."""
    restaurant_names = set()
    
    try:
        with open(jsonl_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if 'original_data' in data and 'name' in data['original_data']:
                        name = data['original_data']['name'].strip()
                        if name:
                            restaurant_names.add(name)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON line: {e}")
                    continue
    except FileNotFoundError:
        print(f"File not found: {jsonl_file_path}")
        return set()
    
    return restaurant_names

def save_restaurant_names_go(restaurant_names, output_file):
    """Save restaurant names as a Go slice."""
    go_content = """package config

// WhitelistedRestaurants contains the list of restaurant names that should be displayed
// This file is auto-generated from llm_processing/restaurant_names.json
// DO NOT EDIT MANUALLY - run llm_processing/generate_restaurant_whitelist.py instead
var WhitelistedRestaurants = []string{
"""
    
    for name in sorted(restaurant_names):
        # Escape quotes and backslashes for Go string literals
        escaped_name = name.replace('\\', '\\\\').replace('"', '\\"')
        go_content += f'\t"{escaped_name}",\n'
    
    go_content += "}\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(go_content)

def save_restaurant_names_json(restaurant_names, output_file):
    """Save restaurant names as JSON for CI/CD pipeline."""
    data = {
        "meta": {
            "total_restaurants": len(restaurant_names),
            "generated_from": "../outputs/review_counts_parsed.jsonl",
            "description": "Restaurant whitelist for backend filtering"
        },
        "restaurants": sorted(list(restaurant_names))
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # Paths - relative to llm_processing folder
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    jsonl_file = project_root / "outputs" / "review_counts_parsed.jsonl"
    
    # Output paths - now in llm_processing for CI/CD
    json_output = script_dir / "restaurant_names.json"
    go_output = project_root / "server" / "internal" / "config" / "restaurant_whitelist.go"
    
    print(f"Reading from: {jsonl_file}")
    restaurant_names = extract_restaurant_names(jsonl_file)
    
    if not restaurant_names:
        print("No restaurant names found!")
        return
    
    print(f"Found {len(restaurant_names)} unique restaurant names")
    
    # Create config directory if it doesn't exist
    go_output.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON in llm_processing (for CI/CD)
    save_restaurant_names_json(restaurant_names, json_output)
    print(f"Saved JSON data to: {json_output}")
    
    # Save as Go file
    save_restaurant_names_go(restaurant_names, go_output)
    print(f"Saved Go whitelist to: {go_output}")
    
    # Print some examples
    print("\nExample restaurant names:")
    for i, name in enumerate(sorted(restaurant_names)[:10]):
        print(f"  {i+1}. {name}")
    if len(restaurant_names) > 10:
        print(f"  ... and {len(restaurant_names) - 10} more")

if __name__ == "__main__":
    main()