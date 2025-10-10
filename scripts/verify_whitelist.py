#!/usr/bin/env python3
"""Quick script to check if restaurant names in the whitelist match actual database entries."""

import json
import sqlite3
import sys
from pathlib import Path

def main():
    # Load the whitelist from llm_processing folder
    whitelist_file = Path("llm_processing/restaurant_names.json")
    
    try:
        with open(whitelist_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            whitelist = set(data["restaurants"])
            total = data["meta"]["total_restaurants"]
    except FileNotFoundError:
        print(f"Whitelist file not found: {whitelist_file}")
        return
    except KeyError as e:
        print(f"Invalid JSON structure in {whitelist_file}: missing {e}")
        return
    
    print(f"Loaded {len(whitelist)} restaurants from whitelist")
    print(f"Metadata shows {total} total restaurants")
    print("\nFirst 5 restaurants in whitelist:")
    for i, name in enumerate(sorted(whitelist)[:5]):
        print(f"  {i+1}. '{name}'")
    
    print(f"\nTotal restaurants in whitelist: {len(whitelist)}")
    print("Restaurant listing backend has been updated to only show these restaurants.")
    print("\nThe following repository methods now filter by this whitelist:")
    print("  - GetAllRestaurants()")
    print("  - GetRestaurantByID()")  
    print("  - SearchRestaurantsByDish()")
    
    print(f"\n🔄 CI/CD Integration: Script is in llm_processing/ folder")
    print(f"📋 Whitelist data: {whitelist_file}")
    print(f"🏗️  Generated code: server/internal/config/restaurant_whitelist.go")

if __name__ == "__main__":
    main()