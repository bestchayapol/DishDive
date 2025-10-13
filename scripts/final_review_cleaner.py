#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final review cleaner:
- Reads from outputs/complex_reviews.csv and outputs/simple_reviews.csv (if present)
- Extracts ONE complete review per row from polluted review_text
- Removes UI/navigation, controls, ads, other reviewers, hashtags
- Keeps: title (if any), ราคาต่อหัว, เมนูเด็ด, full body text
- Outputs two columns: restaurant_name, review_text
- Deduplicates exact and truncation/near-duplicate pairs within same restaurant
"""

import re
import sys
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Optional, Tuple

import pandas as pd


UI_BOUNDARIES = [
    r"^ตัวกรอง$",
    r"^เรียงตาม$",
    r"^กดเพื่อดูรีวิวอื่นๆ เพิ่มเติม.*$",
    r"^อ่านรีวิวร้านอื่นๆ ที่สมาชิกวงในแนะนำ$",
    r"^Share$",
    r"^0 Comment$",
    r"^\d+ Like[s]?$",
    r"^\d+ Comment[s]?$",
    r"^Like$",
    r"^Comment$",
    r"^Ad ·.*$",
]

UI_NOISE_LINES = [
    r"^บันทึก$",
    r"^Quality Review$",
    r"^ยืนยันตัวตนแล้ว$",
    r"^ดูแล้ว \d+.*$",
    r"^เมื่อ .*$",
    r"^\+\d+$",
    r"^[0-9]+(\.[0-9]+)?k$",
    r"^\d+(\.\d+)?$",
    r"^\d+ เรตติ้ง.*$",
    r"^อาหาร[\u0E00-\u0E7F\w\s/]+$",  # category line often short
    r"^•$",
    r"^฿+.*$",
    r"^เปิดอยู่.*$",
    r"^ปิดอยู่.*$",
    r"^จนถึง .*$",
    r"^จะเปิดในเวลา .*$",
    r"^ดูเพิ่มเติม$",
]

HASHTAG_PATTERN = re.compile(r"(?m)^#.+$")
AD_BLOCK_START = re.compile(r"(?m)^Ad ·.*$")


def strip_breadcrumbs(text: str) -> str:
    # Remove top breadcrumbs up to the first occurrence of a restaurant name repeat or "รีวิว"
    # Heuristic: cut everything up to the first line that looks like a reviewer name or until after 'รีวิว <name>'
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove everything from start until a line that looks like a review title or price/menu lines appear
    # We'll search for the first marker among: 'ราคาต่อหัว:', 'เมนูเด็ด:', 'Quality Review', or a typical title-like line
    markers = [
        r"ราคาต่อหัว:\s*",
        r"เมนูเด็ด:\s*",
        r"Quality Review",
    ]
    idx = len(text)
    for pat in markers:
        m = re.search(pat, text)
        if m:
            idx = min(idx, m.start())
    # If found any marker, backtrack to a safe line start
    if idx < len(text):
        start = text.rfind("\n", 0, idx)
        if start != -1:
            return text[start + 1 :]
    return text


def split_into_candidate_blocks(text: str) -> List[str]:
    """Split text into reviewer blocks using Thai UI markers as boundaries."""
    lines = [ln.strip() for ln in text.split("\n")]
    # Remove empty lines early
    lines = [ln for ln in lines if ln]

    # Remove ad blocks fully: from 'Ad ·' until next blank or next 'Ad ·'
    cleaned: List[str] = []
    skip = False
    for ln in lines:
        if AD_BLOCK_START.match(ln):
            skip = True
            continue
        if skip and (ln.startswith("฿") or ln.startswith("Starbucks") or re.match(r"^[A-Za-zก-๙].*", ln) and len(ln) > 40):
            # heuristic end of ad section once a normal long line appears
            skip = False
        if not skip:
            cleaned.append(ln)

    # Remove obvious UI noise lines
    def is_ui_noise(s: str) -> bool:
        return any(re.match(pat, s) for pat in UI_NOISE_LINES)

    cleaned = [ln for ln in cleaned if not is_ui_noise(ln)]
    # Remove hashtags
    cleaned = [ln for ln in cleaned if not ln.startswith('#')]

    # Now split into blocks by boundaries indicating new reviewer or controls
    boundaries = [re.compile(pat) for pat in UI_BOUNDARIES]
    blocks: List[List[str]] = [[]]
    for ln in cleaned:
        if any(b.match(ln) for b in boundaries):
            if blocks[-1]:
                blocks.append([])
            continue
        # Heuristic: a reviewer header often looks like a display name followed by numbers lines; we keep it, but blocks split when "ตัวกรอง" etc seen
        blocks[-1].append(ln)

    # Convert to strings and drop tiny blocks
    blocks_s = ["\n".join(b).strip() for b in blocks if len("".join(b)) > 40]
    return blocks_s


def score_block(block: str) -> int:
    score = 0
    # Reward presence of key fields
    if "ราคาต่อหัว:" in block:
        score += 5
    if "เมนูเด็ด:" in block:
        score += 5
    # Reward reasonable Thai content length
    thai_chars = len(re.findall(r"[ก-๙]", block))
    score += min(thai_chars // 50, 20)  # up to +20
    # Penalize if contains many UI controls leftovers
    if "ตัวกรอง" in block or "เรียงตาม" in block:
        score -= 5
    # Penalize if too short/too long
    n = len(block)
    if n < 120:
        score -= 10
    if n > 8000:
        score -= 5
    return score


def format_block(block: str) -> Optional[str]:
    """Format a candidate block to desired output structure and trim trailing UI noise."""
    # Remove trailing controls if any
    lines = [ln.strip() for ln in block.split("\n")]

    # Drop lines that are pure controls or social actions
    def drop_line(ln: str) -> bool:
        if re.match(r"^(Like|Share|Comment|0 Comment|\d+ Likes?)$", ln):
            return True
        if ln.startswith("ตัวกรอง") or ln.startswith("เรียงตาม"):
            return True
        if ln.startswith("อ่านต่อ") or ln.endswith("อ่านต่อ"):
            return True
        if ln.startswith("ดูเพิ่มเติม") or ln.endswith("ดูเพิ่มเติม"):
            return True
        if ln.startswith("Ad ·"):
            return True
        if ln.startswith('#'):
            return True
        return False

    lines = [ln for ln in lines if ln and not drop_line(ln)]

    if not lines:
        return None

    # Keep only content from first occurrence of title/price/menu to before another reviewer-like header
    # Find the first index of either title (non-UI line), 'ราคาต่อหัว:' or 'เมนูเด็ด:'
    start_idx = 0
    for i, ln in enumerate(lines):
        if 'ราคาต่อหัว:' in ln or 'เมนูเด็ด:' in ln or re.search(r"[ก-๙]{6,}", ln):
            start_idx = i
            break

    # Trim after social controls
    end_idx = len(lines)
    for i, ln in enumerate(lines[start_idx:], start=start_idx):
        if re.match(r"^(0 Like|0 Comment|\d+ Like|\d+ Comment)$", ln):
            end_idx = i
            break

    lines = lines[start_idx:end_idx]

    # Ensure we keep only one contiguous review: stop at a line that looks like the next reviewer's metrics (e.g., numbers-only lines or verified lines)
    pruned: List[str] = []
    for ln in lines:
        if re.match(r"^\d+[kK]?$", ln):
            break
        if ln == 'ยืนยันตัวตนแล้ว':
            break
        pruned.append(ln)

    text = "\n".join(pruned).strip()
    # Minimal validation: needs some Thai text and at least 2 lines
    if len(re.findall(r"[ก-๙]", text)) < 30:
        return None
    if text.count("\n") < 2:
        return None
    return text


def extract_single_review(raw_text: str) -> Optional[str]:
    if not isinstance(raw_text, str) or not raw_text.strip():
        return None
    t = strip_breadcrumbs(raw_text)
    blocks = split_into_candidate_blocks(t)
    if not blocks:
        return None
    # Choose best-scoring block
    best = max(blocks, key=score_block)
    return format_block(best)


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    # Exact duplicates
    df = df.drop_duplicates(subset=['restaurant_name', 'review_text']).reset_index(drop=True)
    # Within-restaurant truncation/near-duplicate removal
    to_drop = set()
    for rest, group in df.groupby('restaurant_name'):
        rows = list(group.itertuples())
        for i in range(len(rows)):
            if rows[i].Index in to_drop:
                continue
            for j in range(i + 1, len(rows)):
                if rows[j].Index in to_drop:
                    continue
                t1, t2 = rows[i].review_text.strip(), rows[j].review_text.strip()
                # truncation
                short, long = (t1, t2) if len(t1) < len(t2) else (t2, t1)
                if short and short in long:
                    to_drop.add(rows[i].Index if len(t1) < len(t2) else rows[j].Index)
                    continue
                # near-duplicate
                if similarity(t1, t2) >= 0.92:
                    to_drop.add(rows[i].Index if len(t1) < len(t2) else rows[j].Index)
    if to_drop:
        df = df.drop(index=list(to_drop)).reset_index(drop=True)
    return df


def load_csv_if_exists(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, encoding='utf-8')
        return df
    except Exception:
        # Try fallback
        return pd.read_csv(path)


def main():
    # Resolve workspace root (handle being in scripts/)
    script_dir = Path(__file__).resolve().parent
    candidate_root = script_dir
    if not (candidate_root / 'outputs').exists() and (candidate_root.parent / 'outputs').exists():
        candidate_root = candidate_root.parent
    root = candidate_root
    input_complex = root / 'outputs' / 'complex_reviews.csv'
    input_simple = root / 'outputs' / 'simple_reviews.csv'
    out_file = root / 'reviews_cleaned_final_v2.csv'
    inter_file = root / 'reviews_cleaned_intermediate_v2.csv'
    dedup_diag_file = root / 'reviews_dedup_diagnostics_v2.csv'

    dfs: List[pd.DataFrame] = []
    for p in [input_complex, input_simple]:
        df = load_csv_if_exists(p)
        if df is None:
            continue
        # Require columns
        if 'restaurant_name' not in df.columns or 'review_text' not in df.columns:
            print(f"Skipping {p.name}: required columns missing")
            continue
        src_label = 'complex' if p.name.startswith('complex_') else ('simple' if p.name.startswith('simple_') else p.stem)
        tmp = df[['restaurant_name', 'review_text']].copy()
        tmp['source'] = src_label
        dfs.append(tmp)

    if not dfs:
        print("No input CSVs found.")
        sys.exit(1)

    src = pd.concat(dfs, ignore_index=True)
    print(f"Loaded rows: {len(src)} from {len(dfs)} file(s)")
    by_source = src.groupby('source').size().to_dict()
    print(f"By source (raw): {by_source}")

    # Extract clean text per row
    src['cleaned'] = src['review_text'].apply(extract_single_review)
    cleaned = src.dropna(subset=['cleaned']).copy()
    cleaned['original_review_text'] = cleaned['review_text']
    cleaned['review_text'] = cleaned['cleaned']
    cleaned = cleaned.drop(columns=['cleaned'])
    cleaned['cleaned_length'] = cleaned['review_text'].astype(str).str.len()
    cleaned['raw_length'] = cleaned['original_review_text'].astype(str).str.len()
    cleaned = cleaned.reset_index(drop=True)

    print(f"Successfully extracted: {len(cleaned)}")
    print(f"By source (extracted): {cleaned.groupby('source').size().to_dict()}")

    # Deduplicate
    # Diagnostics-aware deduplication
    before = len(cleaned)
    # attach a stable row_id for diagnostics
    cleaned = cleaned.reset_index(drop=False).rename(columns={'index': 'row_id'})

    # Copy of deduplicate to capture reasons
    def deduplicate_with_diagnostics(df: pd.DataFrame):
        from typing import List, Dict, Tuple
        df2 = df.drop_duplicates(subset=['restaurant_name', 'review_text']).reset_index(drop=True)
        diag: List[Dict] = []
        to_drop = set()
        for rest, group in df2.groupby('restaurant_name'):
            rows = list(group.itertuples())
            for i in range(len(rows)):
                if rows[i].Index in to_drop:
                    continue
                for j in range(i + 1, len(rows)):
                    if rows[j].Index in to_drop:
                        continue
                    t1, t2 = rows[i].review_text.strip(), rows[j].review_text.strip()
                    # truncation (conservative: only if shorter is a prefix and length ratio <= 0.9)
                    short, long = (t1, t2) if len(t1) < len(t2) else (t2, t1)
                    reason = None
                    simv = None
                    if short and long.startswith(short.rstrip(' .…')) and len(short) <= 0.9 * len(long):
                        # remove shorter
                        drop_idx = rows[i].Index if len(t1) < len(t2) else rows[j].Index
                        to_drop.add(drop_idx)
                        reason = 'truncation_prefix'
                    else:
                        simv = similarity(t1, t2)
                        if simv >= 0.975:
                            drop_idx = rows[i].Index if len(t1) < len(t2) else rows[j].Index
                            to_drop.add(drop_idx)
                            reason = 'near_duplicate'
                    if reason:
                        a, b = (rows[i], rows[j])
                        diag.append({
                            'restaurant_name': rest,
                            'row_id_a': a.row_id,
                            'row_id_b': b.row_id,
                            'len_a': len(t1),
                            'len_b': len(t2),
                            'source_a': a.source,
                            'source_b': b.source,
                            'reason': reason,
                            'similarity': simv,
                        })
        if to_drop:
            df2 = df2.drop(index=list(to_drop)).reset_index(drop=True)
        return df2, diag

    cleaned_before_dedup = cleaned.copy()
    cleaned_dedup, diag = deduplicate_with_diagnostics(cleaned)
    after = len(cleaned_dedup)
    print(f"Deduplicated: removed {before - after} duplicates; final {after}")
    print(f"By source (final): {cleaned_dedup.groupby('source').size().to_dict()}")

    # Save
    # Save final two-column output
    cleaned_dedup[['restaurant_name', 'review_text']].to_csv(out_file, index=False, encoding='utf-8')
    print(f"Saved: {out_file}")

    # Save intermediate (with source/lengths) and dedup diagnostics
    cleaned_before_dedup[['row_id','restaurant_name','source','raw_length','cleaned_length','review_text']].to_csv(inter_file, index=False, encoding='utf-8')
    pd.DataFrame(diag).to_csv(dedup_diag_file, index=False, encoding='utf-8')
    print(f"Saved intermediate: {inter_file}")
    print(f"Saved dedup diagnostics: {dedup_diag_file}")

    # Quick check against provided sample files if present
    sample_in = root / 'sample_review_text.txt'
    sample_out = root / 'cleaned_review_example.txt'
    if sample_in.exists() and sample_out.exists():
        raw = sample_in.read_text(encoding='utf-8', errors='ignore')
        extracted = extract_single_review(raw)
        if extracted:
            expected = sample_out.read_text(encoding='utf-8', errors='ignore').strip()
            sim = similarity(extracted, expected)
            print(f"Sample similarity vs expected: {sim:.3f}")
            print("Extracted sample (first 300 chars):\n" + extracted[:300])
        else:
            print("Could not extract from sample_review_text.txt")


if __name__ == '__main__':
    main()
