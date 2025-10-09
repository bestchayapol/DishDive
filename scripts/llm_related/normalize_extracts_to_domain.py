import argparse
import json
import logging
import os
import pathlib
import sys
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

import psycopg2
import psycopg2.extras as pg_extras
import re

# Ensure project root in path for config reuse
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_processing.config import Config
from llm_processing.normalize_core import NormalizationContext


def ensure_domain_tables(conn):
    ddl_list = [
        # restaurants
        """
        -- NOTE: removed legacy columns usable_rev / total_rev
        CREATE TABLE IF NOT EXISTS restaurants (
            res_id BIGSERIAL PRIMARY KEY,
            res_name VARCHAR(255) NOT NULL UNIQUE,
            res_cuisine VARCHAR(100),
            res_restriction VARCHAR(100),
            menu_size INT NOT NULL DEFAULT 0,
            image_tag VARCHAR(50)
        );
        """,
        # dishes
        """
        CREATE TABLE IF NOT EXISTS dishes (
            dish_id BIGSERIAL PRIMARY KEY,
            res_id BIGINT NOT NULL REFERENCES restaurants(res_id),
            dish_name VARCHAR(255) NOT NULL,
            cuisine VARCHAR(100),
            restriction VARCHAR(100),
            positive_score INT NOT NULL DEFAULT 0,
            negative_score INT NOT NULL DEFAULT 0,
            total_score DOUBLE PRECISION NOT NULL DEFAULT 0,
            UNIQUE(res_id, dish_name)
        );
        """,
        # keywords
        """
        CREATE TABLE IF NOT EXISTS keywords (
            keyword_id BIGSERIAL PRIMARY KEY,
            keyword VARCHAR(100) NOT NULL,
            category VARCHAR(100) NOT NULL,
            sentiment VARCHAR(50) NOT NULL,
            UNIQUE(keyword, category, sentiment)
        );
        """,
        # dish_keywords
        """
        CREATE TABLE IF NOT EXISTS dish_keywords (
            dish_id BIGINT NOT NULL REFERENCES dishes(dish_id),
            keyword_id BIGINT NOT NULL REFERENCES keywords(keyword_id),
            frequency INT NOT NULL,
            PRIMARY KEY (dish_id, keyword_id)
        );
        """,
        # review_dishes
        """
        CREATE TABLE IF NOT EXISTS review_dishes (
            review_dish_id BIGSERIAL PRIMARY KEY,
            dish_id BIGINT NOT NULL REFERENCES dishes(dish_id),
            res_id BIGINT NOT NULL REFERENCES restaurants(res_id),
            source_id BIGINT NOT NULL,
            source_type VARCHAR(64) NOT NULL DEFAULT 'web'
        );
        """,
        # review_dish_keywords
        """
        CREATE TABLE IF NOT EXISTS review_dish_keywords (
            review_dish_keyword_id BIGSERIAL PRIMARY KEY,
            review_dish_id BIGINT NOT NULL REFERENCES review_dishes(review_dish_id),
            keyword_id BIGINT NOT NULL REFERENCES keywords(keyword_id)
        );
        """,
    ]
    with conn.cursor() as cur:
        for ddl in ddl_list:
            cur.execute(ddl)
        # Create idempotency unique index (safe to attempt repeatedly)
        try:
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_review_dishes_source ON review_dishes (source_type, source_id, dish_id)")
        except Exception:
            pass
    conn.commit()


def load_review_extracts(
    conn,
    source_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
):
    """Yield rows from review_extracts in a deterministic order.

    Parameters
    ----------
    source_type : optional str
        Filter by source_type (case-insensitive) if provided.
    limit : optional int
        Max number of rows to return. None means no limit.
    offset : optional int
        Number of rows to skip from the start (0-based). None means start at 0.
    """
    sql = "SELECT rev_ext_id, source_id, source_type, data_extract FROM review_extracts"
    args: List[Any] = []
    if source_type:
        sql += " WHERE LOWER(source_type) = LOWER(%s)"
        args.append(source_type)
    sql += " ORDER BY rev_ext_id"  # ensure stable ordering for batching
    # Apply LIMIT/OFFSET last
    if limit is not None:
        sql += " LIMIT %s"
        args.append(limit)
    if offset is not None and offset > 0:
        sql += " OFFSET %s"
        args.append(offset)
    with conn.cursor() as cur:
        cur.execute(sql, args)
        for rev_ext_id, source_id, s_type, data_extract in cur.fetchall():
            yield rev_ext_id, source_id, s_type, data_extract


def safe_json_array(val: Any) -> List[dict]:
    """Return a list parsed from a JSON value that may be a string or already a Python list.
    If the value is a dict or anything else, return [].
    """
    try:
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            arr = json.loads(val)
            return arr if isinstance(arr, list) else []
        # Psycopg2 may already parse json to Python types depending on settings
        return []
    except Exception:
        return []


def get_or_create_restaurant(conn, cache: Dict[str, int], name: str) -> int:
    if name in cache:
        return cache[name]
    with conn.cursor() as cur:
        cur.execute("SELECT res_id FROM restaurants WHERE res_name=%s", (name,))
        row = cur.fetchone()
        if row:
            res_id = int(row[0])
            cache[name] = res_id
            return res_id
        # Provide explicit zeros for NOT NULL columns without defaults
        cur.execute(
            "INSERT INTO restaurants (res_name, menu_size) VALUES (%s, %s) RETURNING res_id",
            (name, 0),
        )
        res_id = int(cur.fetchone()[0])
        cache[name] = res_id
        conn.commit()
        return res_id


def get_or_create_dish(conn, cache: Dict[Tuple[int, str], int], res_id: int, dish_name: str, cuisine: Optional[str], restriction: Optional[str]) -> int:
    key = (res_id, dish_name)
    if key in cache:
        return cache[key]
    with conn.cursor() as cur:
        cur.execute("SELECT dish_id FROM dishes WHERE res_id=%s AND dish_name=%s", (res_id, dish_name))
        row = cur.fetchone()
        if row:
            dish_id = int(row[0])
            cache[key] = dish_id
            # Optionally update cuisine/restriction if newly known
            if cuisine or restriction:
                cur.execute(
                    "UPDATE dishes SET cuisine=COALESCE(%s,cuisine), restriction=COALESCE(%s,restriction) WHERE dish_id=%s",
                    (cuisine, restriction, dish_id),
                )
                conn.commit()
            return dish_id
        cur.execute(
            """
            INSERT INTO dishes (res_id, dish_name, cuisine, restriction, positive_score, negative_score, total_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING dish_id
            """,
            (res_id, dish_name, cuisine, restriction, 0, 0, 0.0),
        )
        dish_id = int(cur.fetchone()[0])
        cache[key] = dish_id
        conn.commit()
        return dish_id


def get_or_create_keyword(conn, cache: Dict[Tuple[str, str, str], int], word: str, category: str, sentiment: str) -> int:
    key = (word, category, sentiment)
    if key in cache:
        return cache[key]
    with conn.cursor() as cur:
        cur.execute(
            "SELECT keyword_id FROM keywords WHERE keyword=%s AND category=%s AND sentiment=%s",
            (word, category, sentiment),
        )
        row = cur.fetchone()
        if row:
            keyword_id = int(row[0])
            cache[key] = keyword_id
            return keyword_id
        cur.execute(
            "INSERT INTO keywords (keyword, category, sentiment) VALUES (%s,%s,%s) RETURNING keyword_id",
            (word, category, sentiment),
        )
        keyword_id = int(cur.fetchone()[0])
        cache[key] = keyword_id
        conn.commit()
        return keyword_id


def bump_dish_keyword(conn, dish_id: int, keyword_id: int, inc: int = 1):
    with conn.cursor() as cur:
        # Try update first
        cur.execute(
            "UPDATE dish_keywords SET frequency = frequency + %s WHERE dish_id = %s AND keyword_id = %s",
            (inc, dish_id, keyword_id),
        )
        if cur.rowcount == 0:
            # No row existed; insert fresh
            cur.execute(
                "INSERT INTO dish_keywords (dish_id, keyword_id, frequency) VALUES (%s, %s, %s)",
                (dish_id, keyword_id, inc),
            )
    conn.commit()


def insert_review_dish(conn, dish_id: int, res_id: int, source_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO review_dishes (dish_id, res_id, source_id) VALUES (%s, %s, %s) RETURNING review_dish_id",
            (dish_id, res_id, source_id),
        )
        rdid = int(cur.fetchone()[0])
    conn.commit()
    return rdid


def insert_review_dish_keywords(conn, rdid: int, keyword_ids: List[int]):
    if not keyword_ids:
        return
    rows = [(rdid, kid) for kid in keyword_ids]
    with conn.cursor() as cur:
        pg_extras.execute_values(
            cur,
            "INSERT INTO review_dish_keywords (review_dish_id, keyword_id) VALUES %s",
            rows,
        )
    conn.commit()


def recompute_dish_scores(conn):
    # Per-review scoring (each review counts at most once per polarity)
    with conn.cursor() as cur:
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
    conn.commit()


def recompute_restaurant_stats(conn):
    # menu_size: number of distinct dishes per restaurant
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE restaurants r
            SET menu_size = COALESCE(s.cnt,0)
            FROM (
                SELECT res_id, COUNT(*) AS cnt
                FROM dishes
                GROUP BY res_id
            ) s
            WHERE s.res_id = r.res_id
            """
        )
    conn.commit()

    # res_cuisine/res_restriction by 80% majority across that restaurant's dishes
    with conn.cursor() as cur:
        # Cuisine
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
        # Restriction
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
    conn.commit()


def categorize_keyword(token: str, default_sentiment: str) -> Tuple[str, str]:
    """Categorize a token from sentiment lists into one of
    cuisine | restriction | cost | flavor | others, with sentiment in {positive, negative, neutral}.

    default_sentiment comes from the list we found it in ("positive" or "negative").
    """
    t = (token or "").strip().lower()
    if not t:
        return ("others", default_sentiment)

    # Cost cues
    COST_POS = {
        "ถูก","ไม่แพง","คุ้ม","คุ้มค่า","คุ้มราคา","ราคาดี","ราคาถูก","ราคาคุ้มค่า","คุ้มจริง","คุ้มมาก","ราคาสมเหตุสมผล","สมราคา"
    }
    COST_NEG = {
        "แพง","ราคาแพง","ไม่คุ้ม","ไม่คุ้มค่า","เกินราคา","ราคาแรง","แพงไป","แพงมาก"
    }

    # Flavor cues (taste/texture/presentation). These will be the most common from LLM outputs.
    FLAVOR_POS = {
        "อร่อย","ดี","ดีมาก","เด็ด","แซ่บ","กรอบ","นุ่ม","หอม","เข้มข้น","สด","หวาน","กลมกล่อม","เด้ง","ฉ่ำ","ละมุน","หอมนุ่ม"
    }
    FLAVOR_NEG = {
        "เค็ม","จืด","คาว","เหนียว","หวานไป","เผ็ดไป","ไม่อร่อย","มันไป","เลี่ยน","ไหม้","ดิบ","แฉะ"
    }

    if t in COST_POS:
        return ("cost", "positive")
    if t in COST_NEG:
        return ("cost", "negative")
    if t in FLAVOR_POS:
        return ("flavor", "positive")
    if t in FLAVOR_NEG:
        return ("flavor", "negative")

    # Fallback: if token contains explicit cost words
    if any(k in t for k in ["ราคา","คุ้ม","แพง","ถูก"]):
        # Respect default_sentiment for polarity
        return ("cost", default_sentiment if default_sentiment in {"positive","negative"} else "neutral")

    # Default to others, carry provided sentiment
    if default_sentiment in {"positive","negative"}:
        return ("others", default_sentiment)
    return ("others", "neutral")


def process(
    conn,
    source_type_filter: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    logger: Optional[logging.Logger] = None,
    progress_every: int = 250,
):
    logger = logger or logging.getLogger("normalize")

    ensure_domain_tables(conn)
    ctx = NormalizationContext(conn, logger)
    import os
    debug_mode = os.getenv("DEBUG_NORMALIZE", "0").lower() in ("1","true","yes")
    debug_samples = 0
    debug_limit = 15  # max rows to emit detailed diagnostics

    # Pre-count rows for progress (respect filter, offset/limit)
    with conn.cursor() as cur:
        count_sql = "SELECT COUNT(*) FROM review_extracts"
        c_args: List[Any] = []
        if source_type_filter:
            count_sql += " WHERE LOWER(source_type)=LOWER(%s)"
            c_args.append(source_type_filter)
        cur.execute(count_sql, c_args)
        total_candidate = int(cur.fetchone()[0] or 0)
    # Apply offset/limit to determine target slice
    if offset:
        slice_base = max(total_candidate - offset, 0) if False else total_candidate  # placeholder not used
    target_total = total_candidate
    if offset:
        target_total = max(target_total - offset, 0)
    if limit is not None:
        target_total = min(target_total, limit)
    if target_total <= 0:
        logger.info("No rows to process (target_total=%s)", target_total)
        return
    logger.info("Starting normalization slice: target_rows=%d (progress every %d extracts)", target_total, progress_every)

    # Derive an adaptive progress frequency so small batches still show incremental updates.
    if progress_every <= 0:
        effective_every = 0
    else:
        if target_total <= progress_every:
            # Aim for ~20 updates max (every 5%); at least every row if very tiny.
            effective_every = max(1, target_total // 20 or 1)
        else:
            effective_every = progress_every
    logger.debug("Adaptive progress: requested=%s effective=%s target_total=%s", progress_every, effective_every, target_total)

    start_ts = time.time()
    total_rows = 0  # extraction rows encountered in slice
    processed_rows = 0  # extraction rows with at least one dish
    created_dishes = created_keywords = upsert_dish_keywords = created_review_dishes = 0
    for idx, (rev_ext_id, source_id, s_type, data_extract) in enumerate(
        load_review_extracts(conn, source_type_filter, limit=limit, offset=offset)
    ):
        total_rows += 1
        ctx.current_source_type = s_type or (source_type_filter or 'web')
        ctx_stats = ctx.normalize_extract_row(source_id, data_extract)
        if debug_mode and not ctx_stats.get("processed") and debug_samples < debug_limit:
            # Inspect JSON to explain why skipped
            try:
                arr = json.loads(data_extract) if data_extract else []
            except Exception:
                arr = f"<parse_error len={len(data_extract or '')}>"
            reason = []
            if isinstance(arr, list):
                if not arr:
                    reason.append("empty_array")
                else:
                    # look at first few items
                    problems = []
                    for i, it in enumerate(arr[:3]):
                        if not isinstance(it, dict):
                            problems.append(f"item{i}:not_dict")
                            continue
                        r = (it.get("restaurant") or '').strip()
                        d = (it.get("dish") or '').strip()
                        if not r: problems.append(f"item{i}:no_restaurant")
                        if not d: problems.append(f"item{i}:no_dish")
                    if problems:
                        reason.extend(problems)
                    else:
                        reason.append("all_items_filtered? (unexpected)")
            else:
                reason.append("not_list_json")
            logger.warning("DEBUG skip rev_ext_id=%s source_id=%s reasons=%s sample=%r", rev_ext_id, source_id, ','.join(reason), (data_extract or '')[:160])
            debug_samples += 1
        if ctx_stats.get("processed"):
            processed_rows += 1
        created_dishes += ctx_stats.get("created_dishes", 0)
        created_keywords += ctx_stats.get("created_keywords", 0)
        upsert_dish_keywords += ctx_stats.get("dish_kw_links", 0)
        created_review_dishes += ctx_stats.get("review_dishes", 0)

        # Progress logging (adaptive). Always log first row if more remain.
        if effective_every > 0 and (total_rows == 1 or total_rows % effective_every == 0 or total_rows == target_total):
            elapsed = time.time() - start_ts
            pct = (total_rows / target_total) * 100 if target_total else 100.0
            rate = total_rows / elapsed if elapsed > 0 else 0
            remaining = target_total - total_rows
            eta_sec = remaining / rate if rate > 0 else 0
            logger.info(
                "Progress %d/%d (%.1f%%) dishes_created=%d review_dishes=%d keywords_created=%d dish_kw_links=%d elapsed=%.1fs eta=%.1fs (every %s)",
                total_rows, target_total, pct, created_dishes, created_review_dishes, created_keywords, upsert_dish_keywords, elapsed, eta_sec, effective_every,
            )

    if offset is None:
        eff_offset = 0
    else:
        eff_offset = offset
    elapsed = time.time() - start_ts
    logger.info(
        "Completed slice offset=%d limit=%s -> extracts_seen=%d extracts_with_dishes=%d new_dishes=%d new_keywords=%d dish_kw_links=%d elapsed=%.2fs",
        eff_offset,
        str(limit) if limit is not None else "ALL",
        total_rows,
        processed_rows,
        created_dishes,
        created_keywords,
        upsert_dish_keywords,
        elapsed,
    )

    # Recompute aggregate scores and restaurant metadata
    ctx.recompute_scores_and_restaurants()


def main():
    ap = argparse.ArgumentParser(description="Normalize review_extracts JSON into domain tables.")
    ap.add_argument("--source-type", default=None, help="Filter by source_type (e.g., web)")
    ap.add_argument("--limit", type=int, default=None, help="Limit number of review_extract rows to process")
    ap.add_argument("--offset", type=int, default=None, help="Row offset (start index) for batching")
    ap.add_argument(
        "--start",
        type=int,
        default=None,
        help="Alias for --offset (if both provided, --offset wins)",
    )
    ap.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    ap.add_argument("--progress-every", type=int, default=250, help="Log progress every N review_extract rows (default 250)")
    ap.add_argument("--reset", action="store_true", help="Truncate dish-related domain tables before processing (dishes, dish_keywords, review_dishes, review_dish_keywords)")
    args = ap.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format="[%(levelname)s] %(message)s")
    logger = logging.getLogger("normalize")

    cfg = Config()

    # Direct connection using config (we won't use the pool wrapper here)
    conn = psycopg2.connect(
        host=cfg.pg_host,
        port=cfg.pg_port,
        user=cfg.pg_user,
        password=cfg.pg_password,
        dbname=cfg.pg_database,
        connect_timeout=10,
        sslmode=cfg.pg_sslmode,
    )
    # Resolve offset precedence (offset overrides start if both given)
    resolved_offset = args.offset if args.offset is not None else args.start

    if resolved_offset is not None and resolved_offset < 0:
        logger.error("Offset/start cannot be negative: %d", resolved_offset)
        return

    if args.limit is not None and args.limit <= 0:
        logger.error("Limit must be positive when provided: %d", args.limit)
        return

    try:
        if args.reset:
            logger.warning("--reset specified: truncating domain tables (dishes, dish_keywords, review_dishes, review_dish_keywords)...")
            with conn.cursor() as cur:
                cur.execute("TRUNCATE review_dish_keywords, review_dishes, dish_keywords, dishes RESTART IDENTITY CASCADE")
            conn.commit()
            logger.info("Domain tables truncated.")

        process(
            conn,
            source_type_filter=args.source_type,
            limit=args.limit,
            offset=resolved_offset,
            logger=logger,
            progress_every=args.progress_every,
        )
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
