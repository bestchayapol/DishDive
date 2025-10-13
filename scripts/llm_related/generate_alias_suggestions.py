import argparse
import csv
import logging
import os
import pathlib
import re
import sys
import unicodedata
import json  # was missing previously
from collections import defaultdict, Counter, deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable, Set, Optional

import psycopg2

# Ensure project root path for config reuse (two levels up from scripts/llm_related)
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_processing.config import Config  # noqa: E402

# Optional Thai NLP enhancements (segmentation & phonetic keys)
try:  # pragma: no cover - optional dependency
    from pythainlp import word_tokenize as thai_word_tokenize  # type: ignore
    from pythainlp.soundex import lk82  # type: ignore
except Exception:  # pragma: no cover - if unavailable we degrade gracefully
    thai_word_tokenize = None  # type: ignore
    lk82 = None  # type: ignore

# ---------- Normalization Utilities ----------

def strip_combining(s: str) -> str:
    # Remove combining marks (works for Thai diacritics too)
    return ''.join(ch for ch in unicodedata.normalize('NFKD', s) if not unicodedata.combining(ch))

_THAI_CHAR_RANGE = ('\u0E00', '\u0E7F')

def _contains_thai(s: str) -> bool:
    return any('\u0E00' <= ch <= '\u0E7F' for ch in s)

# Common variant normalizations for high‑frequency Thai dish roots (expand as needed)
_VARIANT_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # กะเพรา / กระเพรา / ผัดกะเพรา / ผัดกระเพรา variations
    (re.compile(r'ผัด?ก[ะ]?ร?ะ?เพร[า]'), 'ผัดกะเพรา'),
    (re.compile(r'ก[ะ]?ร?ะ?เพร[า]'), 'กะเพรา'),
]

def _apply_variant_normalizations(s: str) -> str:
    for pat, repl in _VARIANT_PATTERNS:
        s = pat.sub(repl, s)
    return s

def normalize_text(s: str) -> str:
    s = s.strip().lower()
    s = strip_combining(s)
    s = _apply_variant_normalizations(s)
    # Remove punctuation/symbols (keep letters/numbers/spaces)
    s = re.sub(r'[!"#$%&\'()*+,./:;<=>?@\[\]^`{|}~]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def token_sort_key(s: str) -> str:
    toks = s.split()
    toks.sort()
    return ' '.join(toks)

def _thai_segment(s: str, use_thai_seg: bool) -> List[str]:
    if not use_thai_seg or thai_word_tokenize is None:
        # Fallback: if spaces already present, split; else treat as whole token
        return s.split() if ' ' in s else [s]
    try:
        toks = thai_word_tokenize(s, keep_whitespace=False)  # type: ignore
        # Filter empty & punctuation tokens
        toks = [t for t in toks if t and not re.fullmatch(r'[\W_]+', t)]
        return toks or [s]
    except Exception:
        return s.split() if ' ' in s else [s]

def canonical_form(s: str, use_thai_seg: bool = True, order_insensitive: bool = True) -> str:
    n = normalize_text(s)
    if _contains_thai(n):
        toks = _thai_segment(n, use_thai_seg)
    else:
        toks = n.split()
    if order_insensitive:
        toks = sorted(toks)
    return ' '.join(toks)

def phonetic_key(s: str, use_thai_seg: bool = True) -> Optional[str]:
    if lk82 is None:
        return None
    n = normalize_text(s)
    if not _contains_thai(n):
        return None
    toks = _thai_segment(n, use_thai_seg)
    # Map each token to a Thai soundex code; join sorted for order invariance
    codes = []
    for t in toks:
        try:
            code = lk82(t)  # type: ignore
        except Exception:
            code = ''
        if code:
            codes.append(code)
    if not codes:
        return None
    return ' '.join(sorted(codes))

# ---------- Similarity Metrics ----------

def trigrams(s: str) -> Set[str]:
    if len(s) < 3:
        return {s}
    return {s[i:i+3] for i in range(len(s)-2)}

def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)

def levenshtein_ratio(a: str, b: str) -> float:
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    # DP
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(
                prev[j] + 1,      # deletion
                cur[j-1] + 1,      # insertion
                prev[j-1] + cost   # substitution
            ))
        prev = cur
    dist = prev[-1]
    lmax = max(la, lb)
    return 1 - dist / lmax

# ---------- Data Extraction ----------

def fetch_rows(conn, sql: str) -> Iterable[Tuple]:
    with conn.cursor() as cur:
        cur.execute(sql)
        for row in cur.fetchall():
            yield row

@dataclass
class AliasCandidate:
    cluster_id: int
    canonical: str
    member: str
    support: int  # frequency signal
    proposed: int = 1

# ---------- Clustering ----------

def build_clusters(strings_with_support: List[Tuple[str, int]], jaccard_thr: float, lev_thr: float, *, use_thai_seg: bool = True, enable_phonetic: bool = True) -> List[List[Tuple[str, int]]]:
    # Deduplicate identical strings by taking max support (or sum; choose max to keep strongest signal)
    dedup: Dict[str, int] = {}
    for s, sup in strings_with_support:
        if s in dedup:
            if sup > dedup[s]:
                dedup[s] = sup
        else:
            dedup[s] = sup

    # Precompute forms & optionally phonetic keys
    entries = []  # (original, canonical_form, trigrams, support, phonetic_key)
    for s, sup in dedup.items():
        cf = canonical_form(s, use_thai_seg=use_thai_seg)
        tri = trigrams(cf)
        pk = phonetic_key(s, use_thai_seg=use_thai_seg) if enable_phonetic else None
        entries.append((s, cf, tri, sup, pk))

    # Group by canonical exact to seed clusters
    buckets: Dict[str, List[Tuple[str, str, Set[str], int, Optional[str]]]] = defaultdict(list)
    for e in entries:
        buckets[e[1]].append(e)

    clusters: List[List[Tuple[str, int]]] = []
    visited: Set[str] = set()  # track original strings visited

    # First, add pure exact canonical buckets as initial components
    for cf, rows in buckets.items():
        if len(rows) == 1:
            # We'll still consider it for fuzzy merging below
            continue
        comp = [(r[0], r[3]) for r in rows]
        for r in rows:
            visited.add(r[0])
        clusters.append(comp)

    # Build adjacency for remaining entries not in multi buckets
    remaining = [e for e in entries if e[0] not in visited]

    # Quick index by length to reduce comparisons
    length_index: Dict[int, List[Tuple[str, str, Set[str], int, Optional[str]]]] = defaultdict(list)
    for r in remaining:
        length_index[len(r[1])].append(r)

    # For each remaining string, BFS expand similar ones
    used: Set[str] = set()
    for orig, cf, tri, sup, pk in remaining:
        if orig in used:
            continue
        queue = deque([ (orig, cf, tri, sup, pk) ])
        component: List[Tuple[str, int]] = []
        used.add(orig)
        while queue:
            o2, cf2, tri2, sup2, pk2 = queue.popleft()
            component.append((o2, sup2))
            l = len(cf2)
            candidate_lengths = [l-2, l-1, l, l+1, l+2]
            for cl in candidate_lengths:
                if cl < 1:
                    continue
                for cand in length_index.get(cl, []):
                    o3, cf3, tri3, sup3, pk3 = cand
                    if o3 in used:
                        continue
                    # Fast path: phonetic key exact match (if enabled)
                    if enable_phonetic and pk2 and pk3 and pk2 == pk3:
                        used.add(o3)
                        queue.append(cand)
                        continue
                    # Similarity checks
                    jac = jaccard(tri2, tri3)
                    if jac >= jaccard_thr:
                        used.add(o3)
                        queue.append(cand)
                        continue
                    lev = levenshtein_ratio(cf2, cf3)
                    if lev >= lev_thr:
                        used.add(o3)
                        queue.append(cand)
        clusters.append(component)

    return clusters

# ---------- Canonical Selection ----------

def choose_canonical(cluster: List[Tuple[str, int]]) -> str:
    # cluster: list of (string, support)
    # pick by highest support, then longest, then lexicographic
    cluster_sorted = sorted(cluster, key=lambda x: (-x[1], -len(x[0]), x[0]))
    return cluster_sorted[0][0]

# ---------- Candidate CSV Writers ----------

def write_dish_candidates(path: pathlib.Path, clusters: List[List[Tuple[str, int]]]):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['cluster_id', 'canonical_dish', 'member_dish', 'support_count', 'proposed', 'accept'])
        for cid, comp in enumerate(clusters, 1):
            canonical = choose_canonical(comp)
            for (s, sup) in comp:
                w.writerow([cid, canonical, s, sup, 1, 1 if s == canonical else 0])

def write_keyword_candidates(path: pathlib.Path, clusters_by_cat: Dict[str, List[List[Tuple[str, int]]]]):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['cluster_id', 'category', 'canonical_keyword', 'member_keyword', 'support_count', 'proposed', 'accept'])
        global_cid = 0
        for category, clusters in clusters_by_cat.items():
            for comp in clusters:
                global_cid += 1
                canonical = choose_canonical(comp)
                for (s, sup) in comp:
                    w.writerow([global_cid, category, canonical, s, sup, 1, 1 if s == canonical else 0])


def write_restaurant_location_candidates(path: pathlib.Path, clusters: List[List[Tuple[str, int]]]):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['cluster_id', 'canonical_restaurant', 'raw_restaurant_name', 'canonical_freq', 'raw_freq', 'location_name', 'proposed', 'accept'])
        for cid, comp in enumerate(clusters, 1):
            canonical = choose_canonical(comp)
            canonical_cf = canonical_form(canonical)
            canonical_tokens = canonical_cf.split()
            canonical_freq = next(sup for s, sup in comp if s == canonical)
            for (s, sup) in comp:
                raw_cf = canonical_form(s)
                raw_tokens = raw_cf.split()
                location_tokens = []
                # if raw starts with canonical token sequence, remainder is location
                if raw_tokens[:len(canonical_tokens)] == canonical_tokens and len(raw_tokens) > len(canonical_tokens):
                    location_tokens = raw_tokens[len(canonical_tokens):]
                location_name = ' '.join(location_tokens) if location_tokens else ''
                w.writerow([cid, canonical, s, canonical_freq, sup, location_name, 1, 1 if s == canonical else 0])

# ---------- Main Flow ----------

def main():
    ap = argparse.ArgumentParser(description='Generate alias suggestion CSVs for dishes, keywords, restaurant locations.')
    ap.add_argument('--output-dir', default='alias_candidates', help='Directory to write candidate CSVs')
    ap.add_argument('--jaccard-thr', type=float, default=0.75)
    ap.add_argument('--lev-thr', type=float, default=0.85)
    ap.add_argument('--min-support', type=int, default=1, help='Minimum frequency to include a term')
    ap.add_argument('--no-thai-seg', action='store_true', help='Disable Thai word segmentation even if PyThaiNLP is installed')
    ap.add_argument('--no-phonetic', action='store_true', help='Disable Thai phonetic (lk82) merging')
    ap.add_argument('--log-level', default=os.getenv('LOG_LEVEL', 'INFO'))
    args = ap.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format='[%(levelname)s] %(message)s')
    logger = logging.getLogger('alias_gen')

    out_dir = pathlib.Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = Config()
    conn = psycopg2.connect(
        host=cfg.pg_host,
        port=cfg.pg_port,
        user=cfg.pg_user,
        password=cfg.pg_password,
        dbname=cfg.pg_database,
        connect_timeout=10,
        sslmode=cfg.pg_sslmode,
    )

    try:
        # ----- Dishes -----
        dish_rows = list(fetch_rows(conn, 'SELECT dish_name, dish_id FROM dishes'))
        # support: number of review_dishes referencing that dish (popularity signal)
        dish_support_map: Dict[str, int] = defaultdict(int)
        with conn.cursor() as cur:
            cur.execute('SELECT d.dish_name, COUNT(r.review_dish_id) FROM dishes d LEFT JOIN review_dishes r ON r.dish_id = d.dish_id GROUP BY d.dish_name')
            for name, cnt in cur.fetchall():
                dish_support_map[name] = int(cnt)
        dish_support_list = [(name, dish_support_map.get(name, 0)) for (name, _) in dish_rows if dish_support_map.get(name, 0) >= args.min_support]
        logger.info('Collected %d dish names (>= support %d).', len(dish_support_list), args.min_support)
        dish_clusters = build_clusters(
            dish_support_list,
            args.jaccard_thr,
            args.lev_thr,
            use_thai_seg=not args.no_thai_seg,
            enable_phonetic=not args.no_phonetic,
        )
        logger.info('Generated %d dish clusters.', len(dish_clusters))
        write_dish_candidates(out_dir / 'alias_dish_candidates.csv', dish_clusters)

        # ----- Keywords (cluster per category) -----
        kw_rows = list(fetch_rows(conn, 'SELECT keyword, category, keyword_id FROM keywords'))
        # support: aggregate frequency in dish_keywords
        kw_freq: Dict[str, int] = defaultdict(int)
        with conn.cursor() as cur:
            cur.execute('''SELECT k.keyword, k.category, SUM(dk.frequency) FROM keywords k LEFT JOIN dish_keywords dk ON dk.keyword_id=k.keyword_id GROUP BY k.keyword,k.category''')
            for kw, cat, freq in cur.fetchall():
                kw_freq[(kw, cat)] = int(freq or 0)
        keyword_clusters_by_cat: Dict[str, List[List[Tuple[str, int]]]] = defaultdict(list)
        # bucket by category and cluster separately
        cat_to_support_pairs: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        for kw, cat, _ in kw_rows:
            sup = kw_freq.get((kw, cat), 0)
            if sup >= args.min_support:
                cat_to_support_pairs[cat].append((kw, sup))
        for cat, pairs in cat_to_support_pairs.items():
            clusters = build_clusters(
                pairs,
                args.jaccard_thr,
                args.lev_thr,
                use_thai_seg=not args.no_thai_seg,
                enable_phonetic=not args.no_phonetic,
            )
            keyword_clusters_by_cat[cat] = clusters
            logger.info('Category %s: %d keywords -> %d clusters', cat, len(pairs), len(clusters))
        write_keyword_candidates(out_dir / 'alias_keyword_candidates.csv', keyword_clusters_by_cat)

        # ----- Restaurant raw names from review_extracts JSON -----
        # Pull raw restaurant values again for location/franchise variants.
        raw_rest_counts: Counter = Counter()
        with conn.cursor() as cur:
            cur.execute('SELECT data_extract FROM review_extracts')
            for (data_extract,) in cur.fetchall():
                try:
                    arr = json.loads(data_extract) if isinstance(data_extract, str) else data_extract
                except Exception:
                    arr = []
                if not isinstance(arr, list):
                    continue
                for obj in arr:
                    if not isinstance(obj, dict):
                        continue
                    r = (obj.get('restaurant') or '').strip()
                    if r:
                        raw_rest_counts[r] += 1
        rest_support_list = [(name, cnt) for name, cnt in raw_rest_counts.items() if cnt >= args.min_support]
        logger.info('Collected %d raw restaurant names (>= support %d).', len(rest_support_list), args.min_support)
        rest_clusters = build_clusters(
            rest_support_list,
            args.jaccard_thr,
            args.lev_thr,
            use_thai_seg=not args.no_thai_seg,
            enable_phonetic=not args.no_phonetic,
        )
        logger.info('Generated %d restaurant clusters.', len(rest_clusters))
        write_restaurant_location_candidates(out_dir / 'restaurant_location_candidates.csv', rest_clusters)

        logger.info('Alias candidate CSVs written to %s', out_dir)
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()
