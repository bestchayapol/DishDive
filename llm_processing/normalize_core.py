import json
import ast
import re
from typing import Dict, Tuple, List, Optional, Set
import psycopg2
import psycopg2.extras as pg_extras


def categorize_keyword(token: str, default_sentiment: str) -> Tuple[str, str]:
    t = (token or "").strip().lower()
    if not t:
        return ("others", default_sentiment)
    COST_POS = {"ถูก","ไม่แพง","คุ้ม","คุ้มค่า","คุ้มราคา","ราคาดี","ราคาถูก","ราคาคุ้มค่า","คุ้มจริง","คุ้มมาก","ราคาสมเหตุสมผล","สมราคา"}
    COST_NEG = {"แพง","ราคาแพง","ไม่คุ้ม","ไม่คุ้มค่า","เกินราคา","ราคาแรง","แพงไป","แพงมาก"}
    FLAVOR_POS = {"อร่อย","ดี","ดีมาก","เด็ด","แซ่บ","กรอบ","นุ่ม","หอม","เข้มข้น","สด","หวาน","กลมกล่อม","เด้ง","ฉ่ำ","ละมุน","หอมนุ่ม"}
    FLAVOR_NEG = {"เค็ม","จืด","คาว","เหนียว","หวานไป","เผ็ดไป","ไม่อร่อย","มันไป","เลี่ยน","ไหม้","ดิบ","แฉะ"}
    if t in COST_POS: return ("cost","positive")
    if t in COST_NEG: return ("cost","negative")
    if t in FLAVOR_POS: return ("flavor","positive")
    if t in FLAVOR_NEG: return ("flavor","negative")
    if any(k in t for k in ["ราคา","คุ้ม","แพง","ถูก"]):
        return ("cost", default_sentiment if default_sentiment in {"positive","negative"} else "neutral")
    if default_sentiment in {"positive","negative"}:
        return ("others", default_sentiment)
    return ("others", "neutral")


class NormalizationContext:
    """Shared normalization core used by both bulk and incremental paths.

    Keeps caches and alias map in-memory to avoid reloading on each row.
    """

    def __init__(self, conn: psycopg2.extensions.connection, logger, enable_thai_norm: bool = True):
        self.conn = conn
        self.logger = logger
        self.rest_cache: Dict[str, int] = {}
        self.dish_cache: Dict[Tuple[int, str], int] = {}
        self.kw_cache: Dict[Tuple[str, str, str], int] = {}
        self.alias_map: Dict[str, str] = {}
        self._thai_norm = (lambda s: s)
        # Current source_type context (bulk loop will set per row; incremental sets once)
        self.current_source_type: str = "web"
        # Detect whether review_dishes has source_type column (runtime migration safety)
        self.has_source_type_col = self._detect_source_type_column()
        self._load_alias_map()
        if enable_thai_norm:
            try:
                from pythainlp.util import normalize as thai_norm  # type: ignore
                self._thai_norm = thai_norm
            except Exception:
                pass

    # -------- preload helpers --------
    def _detect_source_type_column(self) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='review_dishes' AND column_name='source_type'
                """)
                return cur.fetchone() is not None
        except Exception:
            return False

    def _load_alias_map(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT d.dish_name, a.alt_name
                    FROM dishes d
                    JOIN dish_aliases a ON a.dish_id = d.dish_id
                    """
                )
                for base, alt in cur.fetchall():
                    base_s = str(base).strip()
                    alt_s = str(alt).strip()
                    if alt_s and base_s and alt_s.lower() != base_s.lower():
                        self.alias_map[alt_s.lower()] = base_s
        except Exception as e:
            self.logger.debug("alias_map preload failed: %s", e)

    # -------- canonicalization --------
    def canonical_dish_name(self, raw: str) -> str:
        s = (raw or "").strip()
        if not s:
            return s
        s = self._thai_norm(s)
        s = re.sub(r"\s+", " ", s)
        low = s.lower()
        if low in self.alias_map:
            return self.alias_map[low]
        if 4 <= len(low) <= 18 and ' ' not in low:
            sig = ''.join(sorted([c for c in low if not re.match(r"[\u0E31\u0E47-\u0E4E]", c)]))
            for k, base in self.alias_map.items():
                ks = ''.join(sorted([c for c in k if not re.match(r"[\u0E31\u0E47-\u0E4E]", c)]))
                if ks == sig:
                    return base
        return s

    # -------- DB entity helpers --------
    def get_or_create_restaurant(self, name: str) -> int:
        if name in self.rest_cache:
            return self.rest_cache[name]
        with self.conn.cursor() as cur:
            cur.execute("SELECT res_id FROM restaurants WHERE res_name=%s", (name,))
            r = cur.fetchone()
            if r:
                rid = int(r[0]); self.rest_cache[name]=rid; return rid
            cur.execute("INSERT INTO restaurants (res_name, menu_size) VALUES (%s,0) RETURNING res_id", (name,))
            rid = int(cur.fetchone()[0]); self.conn.commit(); self.rest_cache[name]=rid; return rid

    def get_or_create_dish(self, res_id: int, dish_name: str, cuisine: Optional[str], restriction: Optional[str]) -> int:
        key = (res_id, dish_name)
        if key in self.dish_cache:
            return self.dish_cache[key]
        with self.conn.cursor() as cur:
            cur.execute("SELECT dish_id FROM dishes WHERE res_id=%s AND dish_name=%s", (res_id,dish_name))
            r = cur.fetchone()
            if r:
                did = int(r[0]); self.dish_cache[key]=did
                if cuisine or restriction:
                    cur.execute("UPDATE dishes SET cuisine=COALESCE(%s,cuisine), restriction=COALESCE(%s,restriction) WHERE dish_id=%s", (cuisine,restriction,did))
                    self.conn.commit()
                return did
            cur.execute("INSERT INTO dishes (res_id,dish_name,cuisine,restriction,positive_score,negative_score,total_score) VALUES (%s,%s,%s,%s,0,0,0.0) RETURNING dish_id", (res_id,dish_name,cuisine,restriction))
            did = int(cur.fetchone()[0]); self.conn.commit(); self.dish_cache[key]=did; return did

    def get_or_create_keyword(self, word: str, category: str, sentiment: str) -> int:
        key = (word, category, sentiment)
        if key in self.kw_cache:
            return self.kw_cache[key]
        with self.conn.cursor() as cur:
            cur.execute("SELECT keyword_id FROM keywords WHERE keyword=%s AND category=%s AND sentiment=%s", (word,category,sentiment))
            r = cur.fetchone()
            if r:
                kid = int(r[0]); self.kw_cache[key]=kid; return kid
            cur.execute("INSERT INTO keywords (keyword,category,sentiment) VALUES (%s,%s,%s) RETURNING keyword_id", (word,category,sentiment))
            kid = int(cur.fetchone()[0]); self.conn.commit(); self.kw_cache[key]=kid; return kid

    def bump_dish_keyword(self, dish_id: int, keyword_id: int, inc: int = 1):
        with self.conn.cursor() as cur:
            cur.execute("UPDATE dish_keywords SET frequency = frequency + %s WHERE dish_id=%s AND keyword_id=%s", (inc,dish_id,keyword_id))
            if cur.rowcount == 0:
                cur.execute("INSERT INTO dish_keywords (dish_id,keyword_id,frequency) VALUES (%s,%s,%s)", (dish_id,keyword_id,inc))
        self.conn.commit()

    def insert_review_dish(self, dish_id: int, res_id: int, source_id: int) -> int:
        """Idempotent insert of review_dish by (source_type, source_id, dish_id)."""
        with self.conn.cursor() as cur:
            if self.has_source_type_col:
                # Try existing
                cur.execute("SELECT review_dish_id FROM review_dishes WHERE source_id=%s AND dish_id=%s AND source_type=%s",
                            (source_id, dish_id, self.current_source_type))
                row = cur.fetchone()
                if row:
                    return int(row[0])
                # Attempt ON CONFLICT path
                try:
                    cur.execute(
                        """
                        INSERT INTO review_dishes (dish_id,res_id,source_id,source_type)
                        VALUES (%s,%s,%s,%s)
                        ON CONFLICT (source_type,source_id,dish_id) DO UPDATE SET res_id=EXCLUDED.res_id
                        RETURNING review_dish_id
                        """,
                        (dish_id, res_id, source_id, self.current_source_type)
                    )
                except Exception as e:
                    # Could be missing unique index; fallback to plain insert (may duplicate once)
                    self.conn.rollback()
                    with self.conn.cursor() as cur2:
                        cur2.execute(
                            "INSERT INTO review_dishes (dish_id,res_id,source_id,source_type) VALUES (%s,%s,%s,%s) RETURNING review_dish_id",
                            (dish_id,res_id,source_id,self.current_source_type)
                        )
                        rdid = int(cur2.fetchone()[0])
                        self.conn.commit()
                        return rdid
                rdid = int(cur.fetchone()[0])
                self.conn.commit(); return rdid
            else:
                # Legacy schema without source_type column
                cur.execute("SELECT review_dish_id FROM review_dishes WHERE source_id=%s AND dish_id=%s",
                            (source_id, dish_id))
                row = cur.fetchone()
                if row:
                    return int(row[0])
                cur.execute("INSERT INTO review_dishes (dish_id,res_id,source_id) VALUES (%s,%s,%s) RETURNING review_dish_id",
                            (dish_id,res_id,source_id))
                rdid = int(cur.fetchone()[0])
                self.conn.commit(); return rdid

    def insert_review_dish_keywords(self, rdid: int, keyword_ids: List[int]):
        if not keyword_ids:
            return
        rows = [(rdid,k) for k in keyword_ids]
        with self.conn.cursor() as cur:
            pg_extras.execute_values(cur, "INSERT INTO review_dish_keywords (review_dish_id, keyword_id) VALUES %s", rows)
        self.conn.commit()

    # -------- main normalization of a single extract row --------
    def normalize_extract_row(self, source_id: int, data_extract) -> Dict[str,int]:  # type: ignore[override]
        """Normalize one review_extract.data_extract blob.

        Accepts either a raw string (JSON or python repr) OR an already-parsed list coming
        from earlier code paths / driver auto-casting. We are defensive here because legacy
        rows were stored as Python list repr with irregular spacing / key corruption.
        """
        # Fast-path: already a list
        arr: List[dict] = []
        salvage_used: Optional[str] = None
        if isinstance(data_extract, list):
            arr = [x for x in data_extract if isinstance(x, dict)]
        else:
            raw = data_extract or ""
            if isinstance(raw, str) and raw.strip():
                # Try strict JSON first
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        arr = [x for x in parsed if isinstance(x, dict)]
                except Exception:
                    # Try python literal
                    try:
                        parsed = ast.literal_eval(raw)
                        if isinstance(parsed, list):
                            arr = [x for x in parsed if isinstance(x, dict)]
                            salvage_used = "ast.literal_eval"
                    except Exception:
                        # Clean up some known corruption patterns then retry literal_eval
                        cleaned = raw
                        cleaned = re.sub(r"'\s+'(thai)'", r"'\1'", cleaned)
                        cleaned = re.sub(r"'cui\s+isine'", "'cuisine'", cleaned)
                        try:
                            parsed = ast.literal_eval(cleaned)
                            if isinstance(parsed, list):
                                arr = [x for x in parsed if isinstance(x, dict)]
                                salvage_used = "cleaned_literal"
                        except Exception:
                            arr = []
        if salvage_used and hasattr(self.logger, 'debug'):
            self.logger.debug("salvaged non-JSON extract source_id=%s via %s", source_id, salvage_used)
        stats = {
            "processed": 0,
            "created_dishes": 0,
            "created_keywords": 0,
            "dish_kw_links": 0,
            "review_dishes": 0,
        }
        if not arr:
            return stats
        for item in arr:
            if not isinstance(item, dict):
                continue
            # Normalize keys with embedded spaces (legacy artifacts) by collapsing whitespace
            norm_item = {}
            for k, v in item.items():
                if isinstance(k, str):
                    nk = re.sub(r"\s+", "", k)
                else:
                    nk = k
                norm_item[nk] = v
            # Sentiment salvage: legacy corruption produced keys like 'p   positive'
            if isinstance(norm_item.get("sentiment"), dict):
                sent_obj = norm_item["sentiment"]
                if isinstance(sent_obj, dict) and ("positive" not in sent_obj or "negative" not in sent_obj):
                    fixed = {"positive": [], "negative": []}
                    for sk, sv in list(sent_obj.items()):
                        if not isinstance(sk, str):
                            continue
                        sk_compact = re.sub(r"\s+", "", sk.lower())
                        if sk_compact.startswith("pos"):
                            fixed["positive"] = sv if isinstance(sv, list) else []
                        elif sk_compact.startswith("neg"):
                            fixed["negative"] = sv if isinstance(sv, list) else []
                    # Only replace if we actually recovered something
                    if fixed["positive"] or fixed["negative"]:
                        norm_item["sentiment"] = fixed
            restaurant = (norm_item.get("restaurant") or "").strip()
            dish_name = (norm_item.get("dish") or "").strip()
            if dish_name:
                dish_name = self.canonical_dish_name(dish_name)
            if not restaurant or not dish_name:
                continue
            cuisine = norm_item.get("cuisine"); cuisine = (str(cuisine).strip().lower() or None) if cuisine is not None else None
            restriction = norm_item.get("restriction"); restriction = (str(restriction).strip().lower() or None) if restriction is not None else None
            res_id = self.get_or_create_restaurant(restaurant)
            pre_dish = len(self.dish_cache)
            dish_id = self.get_or_create_dish(res_id, dish_name, cuisine, restriction)
            if len(self.dish_cache) > pre_dish:
                stats["created_dishes"] += 1
            rdid = self.insert_review_dish(dish_id, res_id, int(source_id))
            stats["review_dishes"] += 1
            rdk_ids: List[int] = []
            if cuisine:
                pre_kw = len(self.kw_cache)
                kid = self.get_or_create_keyword(cuisine, "cuisine", "neutral")
                if len(self.kw_cache) > pre_kw:
                    stats["created_keywords"] += 1
                self.bump_dish_keyword(dish_id, kid, 1); rdk_ids.append(kid)
            if restriction:
                pre_kw = len(self.kw_cache)
                kid = self.get_or_create_keyword(restriction, "restriction", "neutral")
                if len(self.kw_cache) > pre_kw:
                    stats["created_keywords"] += 1
                self.bump_dish_keyword(dish_id, kid, 1); rdk_ids.append(kid)
            sent = norm_item.get("sentiment") or {}
            pos = sent.get("positive") or []
            neg = sent.get("negative") or []
            seen: Set[Tuple[str,str,str]] = set()
            for tok in pos:
                t = str(tok).strip()
                if not t:
                    continue
                cat, senti = categorize_keyword(t, "positive"); key=(t,cat,senti)
                if key in seen: continue
                seen.add(key)
                pre_kw = len(self.kw_cache)
                kid = self.get_or_create_keyword(t, cat, senti)
                if len(self.kw_cache) > pre_kw: stats["created_keywords"] += 1
                self.bump_dish_keyword(dish_id, kid, 1); rdk_ids.append(kid)
            for tok in neg:
                t = str(tok).strip()
                if not t:
                    continue
                cat, senti = categorize_keyword(t, "negative"); key=(t,cat,senti)
                if key in seen: continue
                seen.add(key)
                pre_kw = len(self.kw_cache)
                kid = self.get_or_create_keyword(t, cat, senti)
                if len(self.kw_cache) > pre_kw: stats["created_keywords"] += 1
                self.bump_dish_keyword(dish_id, kid, 1); rdk_ids.append(kid)
            if rdk_ids:
                self.insert_review_dish_keywords(rdid, rdk_ids)
                stats["dish_kw_links"] += len(rdk_ids)
            stats["processed"] = 1
        return stats

    # -------- final recompute (bulk) --------
    def recompute_scores_and_restaurants(self):
        with self.conn.cursor() as cur:
            # Per-review scoring: each review contributes at most 1 positive and/or 1 negative.
            cur.execute(
                """
                WITH per_review AS (
                    SELECT rd.dish_id, rd.review_dish_id,
                           MAX(CASE WHEN k.sentiment='positive' THEN 1 ELSE 0 END) AS has_pos,
                           MAX(CASE WHEN k.sentiment='negative' THEN 1 ELSE 0 END) AS has_neg
                    FROM review_dishes rd
                    LEFT JOIN review_dish_keywords rdk ON rdk.review_dish_id = rd.review_dish_id
                    LEFT JOIN keywords k ON k.keyword_id = rdk.keyword_id
                    GROUP BY rd.dish_id, rd.review_dish_id
                ), agg AS (
                    SELECT dish_id, SUM(has_pos) AS pos, SUM(has_neg) AS neg
                    FROM per_review
                    GROUP BY dish_id
                )
                UPDATE dishes d
                SET positive_score = COALESCE(a.pos,0),
                    negative_score = COALESCE(a.neg,0),
                    total_score = COALESCE(a.pos,0) + COALESCE(a.neg,0)
                FROM agg a
                WHERE a.dish_id = d.dish_id
                """
            )
            cur.execute(
                """
                UPDATE restaurants r SET menu_size=COALESCE(s.cnt,0)
                FROM (SELECT res_id, COUNT(*) AS cnt FROM dishes GROUP BY res_id) s
                WHERE s.res_id=r.res_id
                """
            )
            # Majority cuisine (>=80% of dishes with non-null cuisine)
            cur.execute(
                """
                WITH per_res AS (
                    SELECT res_id, cuisine, COUNT(*) AS cnt,
                           SUM(COUNT(*)) OVER (PARTITION BY res_id) AS total
                    FROM dishes
                    WHERE cuisine IS NOT NULL AND cuisine <> ''
                    GROUP BY res_id, cuisine
                ), pick AS (
                    SELECT res_id, cuisine, cnt, total,
                           ROW_NUMBER() OVER (PARTITION BY res_id ORDER BY cnt DESC) AS rn
                    FROM per_res
                )
                UPDATE restaurants r
                SET res_cuisine = CASE WHEN p.cnt >= 0.8 * p.total THEN p.cuisine ELSE NULL END
                FROM pick p
                WHERE p.res_id = r.res_id AND p.rn = 1
                """
            )
            # Majority restriction (>=80%)
            cur.execute(
                """
                WITH per_res AS (
                    SELECT res_id, restriction, COUNT(*) AS cnt,
                           SUM(COUNT(*)) OVER (PARTITION BY res_id) AS total
                    FROM dishes
                    WHERE restriction IS NOT NULL AND restriction <> ''
                    GROUP BY res_id, restriction
                ), pick AS (
                    SELECT res_id, restriction, cnt, total,
                           ROW_NUMBER() OVER (PARTITION BY res_id ORDER BY cnt DESC) AS rn
                    FROM per_res
                )
                UPDATE restaurants r
                SET res_restriction = CASE WHEN p.cnt >= 0.8 * p.total THEN p.restriction ELSE NULL END
                FROM pick p
                WHERE p.res_id = r.res_id AND p.rn = 1
                """
            )
        self.conn.commit()
