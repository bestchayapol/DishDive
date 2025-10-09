import argparse
import json
import os
import sys
import pandas as pd

# Simple CLI to compute acceptance rate from a processed CSV
# A row is considered accepted if Extracted JSON contains at least one object
# whose dish name passes a basic validity check (same heuristic as pipeline).

INVALID_DISH_TOKENS = set([
    "อร่อย","อร่อยมาก","อร่อยดี","บรรยากาศดี","ราคาไม่แพง","ราคาถูก","ราคาคุ้มค่า","คุ้มค่า","คุ้มราคา","คุณภาพดี","สด","สดๆ","สดมาก","สะอาด","บริการดี","บริการดีมาก","บริการ","หวาน","คาว","เผ็ด","เผ็ดดี","เปรี้ยว","ดีมาก","ดี","ไม่แพง","ผ่าน","แซ่บมาก","แซ่บ","เด็ด","เด็ดมาก"
])
INGREDIENT_ROOTS = set([
    "กุ้ง","หมึก","ปลาหมึก","หมู","ไก่","เนื้อ","ปลา","ปลากะพง","ปลาคัง","ข้าว","วุ้นเส้น","เต้าหู้","กระดูกหมู","ปีกไก่","คอหมู","ก้อย","ต้มยำ","ลาบ","ยำ","ผัด","แกง","ซุป","ซอสมะขาม","ปลาหมึกนึ่งมะนาว","ข้าวผัด","กุ้งเผา","ต้มยำกุ้ง","ลาบปลาหมึก","ยำวุ้นเส้นรวมมิตร"
])
WHITELIST_MULTI = set([
    "ปลาหมึกนึ่งมะนาว","ต้มยำกุ้ง","ข้าวผัดกุ้ง","กุ้งเผา","ลาบปลาหมึก","ยำวุ้นเส้นรวมมิตร","แกงป่า","กุ้งซอสมะขาม"
])


def is_valid_dish_name(name: str) -> bool:
    if not isinstance(name, str):
        return False
    n = name.strip()
    if not n:
        return False
    if n in INVALID_DISH_TOKENS:
        return False
    if len(n) < 3 and n not in WHITELIST_MULTI:
        return False
    if n in WHITELIST_MULTI:
        return True
    if not any(r in n for r in INGREDIENT_ROOTS):
        return False
    return True


def parse_array(s: str):
    if not isinstance(s, str) or not s.strip():
        return []
    try:
        arr = json.loads(s)
        return arr if isinstance(arr, list) else []
    except Exception:
        return []


def main():
    p = argparse.ArgumentParser(description="Compute acceptance rate from processed CSV")
    p.add_argument("csv", help="Path to processed_reviews.csv")
    args = p.parse_args()

    if not os.path.exists(args.csv):
        print(f"File not found: {args.csv}", file=sys.stderr)
        sys.exit(2)

    df = pd.read_csv(args.csv, keep_default_na=False)
    total = len(df)
    accepted = 0
    tier_counts = {}
    tier_accepts = {}

    for _, row in df.iterrows():
        tier = row.get("Extraction Tier", "unknown")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        arr = parse_array(row.get("Extracted JSON", ""))
        ok = False
        for it in arr:
            if isinstance(it, dict) and is_valid_dish_name(str(it.get("dish", ""))):
                ok = True
                break
        if ok:
            accepted += 1
            tier_accepts[tier] = tier_accepts.get(tier, 0) + 1

    rate = (accepted / total * 100) if total else 0
    print(f"Total: {total}")
    print(f"Accepted: {accepted}")
    print(f"Acceptance Rate: {rate:.2f}%")
    print("By tier:")
    for t, c in sorted(tier_counts.items(), key=lambda x: x[1], reverse=True):
        ta = tier_accepts.get(t, 0)
        tr = c - ta
        pct = (ta / c * 100) if c else 0
        print(f"  {t:24} count={c:4} accepted={ta:4} rejected={tr:4} rate={pct:5.2f}%")


if __name__ == "__main__":
    main()
