from collections import defaultdict
import difflib
import re

# ==== TEST DATA ====
dishes = [
    "dish 1", "1 dish", "one dish", "fried rice", "fry rice", "pad kra pao",
    "pad krapao", "basil rice", "green curry", "green curry chicken",
    "tom yum", "tom yam", "somtam", "som tam", "papaya salad"
]
keywords = [
    "super tasty", "very tasty", "delicious", "yummy", "yumi",
    "tasty", "taste good", "good taste", "spicy hot", "spicy",
    "hot and spicy", "sweet", "sweetness", "salty", "salt"
]
restaurants = [
    "McDonalds Bangkok", "McDonalds Chiang Mai", "McDonald's Central", 
    "KFC Central", "K.F.C.", "KFC Mall", "Kentucky Fried Chicken",
    "Starbucks Siam", "Starbucks Coffee", "Pizza Hut", "Pizza Hut Express"
]

# ==== CONFIG ====
DISH_THRESHOLD = 0.6      # Lower threshold for dishes
KEYWORD_THRESHOLD = 0.7   # Medium threshold for keywords  
RESTAURANT_THRESHOLD = 0.8 # Higher threshold for restaurants

# ==== FUNCTIONS ====
def preprocess_text(text):
    """Clean and normalize text for better matching."""
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation and extra spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fuzzy_group(items, threshold, preprocessor=None):
    """Group similar strings based on fuzzy matching."""
    groups = []
    used = set()
    
    # Preprocess all items if preprocessor provided
    processed_items = []
    for item in items:
        processed = preprocessor(item) if preprocessor else item.lower()
        processed_items.append(processed)

    for i, name in enumerate(items):
        if i in used:
            continue
        group = [name]
        used.add(i)
        
        for j in range(i + 1, len(items)):
            if j in used:
                continue
            
            # Compare processed versions
            ratio = difflib.SequenceMatcher(
                None, 
                processed_items[i], 
                processed_items[j]
            ).ratio()
            
            if ratio >= threshold:
                group.append(items[j])
                used.add(j)
        groups.append(group)
    return groups

def normalize_restaurant(name):
    """Enhanced cleanup for restaurant franchise detection."""
    name = name.lower()
    
    # Remove common restaurant words
    remove_words = [
        "restaurant", "cafe", "coffee", "bar", "grill", "branch", 
        "location", "express", "shop", "store", "kitchen", "house"
    ]
    
    for word in remove_words:
        name = re.sub(rf'\b{word}\b', '', name)
    
    # Remove punctuation and normalize spaces
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Handle common abbreviations
    name = name.replace("mcdonald s", "mcdonalds")
    name = name.replace("k f c", "kfc") 
    name = name.replace("kentucky fried chicken", "kfc")
    
    return name

def dish_preprocessor(dish):
    """Special preprocessing for dishes."""
    dish = preprocess_text(dish)
    
    # Handle number words
    dish = dish.replace("one", "1")
    dish = dish.replace("two", "2") 
    dish = dish.replace("three", "3")
    
    # Handle common dish variations
    dish = dish.replace("kra pao", "krapao")
    dish = dish.replace("som tam", "somtam")
    dish = dish.replace("tom yam", "tom yum")
    
    return dish

def keyword_preprocessor(keyword):
    """Special preprocessing for keywords."""
    keyword = preprocess_text(keyword)
    
    # Handle common taste variations
    keyword = keyword.replace("yumi", "yummy")
    keyword = keyword.replace("taste good", "tasty")
    keyword = keyword.replace("good taste", "tasty")
    
    return keyword

# ==== MAIN ====
def main():
    print("=== FUZZY MATCHING RESULTS ===\n")
    
    # Dish aliases
    dish_groups = fuzzy_group(dishes, DISH_THRESHOLD, dish_preprocessor)
    print("=== Dish Aliases ===")
    alias_count = 0
    for g in dish_groups:
        if len(g) > 1:
            aliases = ', '.join([f"'{x}'" for x in g[1:]])
            print(f"📍 '{g[0]}' has {len(g)-1} aliases: {aliases}")
            alias_count += len(g) - 1
    if alias_count == 0:
        print("❌ No dish aliases found")
    else:
        print(f"✅ Found {alias_count} dish aliases")

    # Keyword aliases  
    keyword_groups = fuzzy_group(keywords, KEYWORD_THRESHOLD, keyword_preprocessor)
    print("\n=== Keyword Aliases ===")
    alias_count = 0
    for g in keyword_groups:
        if len(g) > 1:
            aliases = ', '.join([f"'{x}'" for x in g[1:]])
            print(f"🏷️  '{g[0]}' has {len(g)-1} aliases: {aliases}")
            alias_count += len(g) - 1
    if alias_count == 0:
        print("❌ No keyword aliases found")
    else:
        print(f"✅ Found {alias_count} keyword aliases")

    # Restaurant franchises
    print("\n=== Restaurant Franchises ===")
    norm_map = defaultdict(list)
    for r in restaurants:
        norm_key = normalize_restaurant(r)
        norm_map[norm_key].append(r)
    
    franchise_count = 0
    for norm, group in norm_map.items():
        if len(group) > 1:
            locations = ', '.join([f"'{x}'" for x in group[1:]])
            print(f"🏪 '{group[0]}' franchise locations: {locations}")
            franchise_count += len(group) - 1
    
    if franchise_count == 0:
        print("❌ No restaurant franchises found")
    else:
        print(f"✅ Found {franchise_count} franchise locations")

    # Debug info
    print(f"\n=== Debug Info ===")
    print(f"Thresholds: Dishes={DISH_THRESHOLD}, Keywords={KEYWORD_THRESHOLD}, Restaurants={RESTAURANT_THRESHOLD}")
    print(f"Total items: {len(dishes)} dishes, {len(keywords)} keywords, {len(restaurants)} restaurants")

if __name__ == "__main__":
    main()