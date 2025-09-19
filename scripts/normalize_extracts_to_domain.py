import argparse
import json
import logging
import os
import pathlib
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

import psycopg2
import psycopg2.extras as pg_extras

# Ensure project root in path for config reuse
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_processing.config import Config


def ensure_domain_tables(conn):
    ddl_list = [
        # restaurants
        """
        CREATE TABLE IF NOT EXISTS restaurants (
            res_id BIGSERIAL PRIMARY KEY,
            res_name VARCHAR(255) NOT NULL UNIQUE,
            res_cuisine VARCHAR(100),
            res_restriction VARCHAR(100),
            menu_size INT NOT NULL DEFAULT 0,
            usable_rev INT NOT NULL DEFAULT 0,
            total_rev INT NOT NULL DEFAULT 0
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
            source_id BIGINT NOT NULL
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
            "INSERT INTO restaurants (res_name, menu_size, usable_rev, total_rev) VALUES (%s, %s, %s, %s) RETURNING res_id",
            (name, 0, 0, 0),
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
    # Update positive/negative/total scores from dish_keywords joined to keywords.sentiment
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH agg AS (
                SELECT dk.dish_id,
                       SUM(CASE WHEN k.sentiment='positive' THEN dk.frequency ELSE 0 END) AS pos,
                       SUM(CASE WHEN k.sentiment='negative' THEN dk.frequency ELSE 0 END) AS neg
                FROM dish_keywords dk
                JOIN keywords k ON k.keyword_id = dk.keyword_id
                GROUP BY dk.dish_id
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
):
    logger = logger or logging.getLogger("normalize")

    ensure_domain_tables(conn)

    rest_cache: Dict[str, int] = {}
    dish_cache: Dict[Tuple[int, str], int] = {}
    kw_cache: Dict[Tuple[str, str, str], int] = {}

    total_rows = 0  # rows fetched from the DB (within limit/offset slice)
    processed_rows = 0  # rows that produced at least one dish/restaurant linkage
    for idx, (rev_ext_id, source_id, s_type, data_extract) in enumerate(
        load_review_extracts(conn, source_type_filter, limit=limit, offset=offset)
    ):
        total_rows += 1
        arr = safe_json_array(data_extract)
        if not arr:
            continue
        for item in arr:
            if not isinstance(item, dict):
                continue
            restaurant = (item.get("restaurant") or "").strip()
            dish_name = (item.get("dish") or "").strip()
            if not restaurant or not dish_name:
                continue
            cuisine = item.get("cuisine")
            if cuisine is not None:
                cuisine = str(cuisine).strip().lower() or None
            restriction = item.get("restriction")
            if restriction is not None:
                restriction = str(restriction).strip().lower() or None

            res_id = get_or_create_restaurant(conn, rest_cache, restaurant)
            dish_id = get_or_create_dish(conn, dish_cache, res_id, dish_name, cuisine, restriction)

            # Create review_dish row for this (dish, review)
            rdid = insert_review_dish(conn, dish_id, res_id, int(source_id))

            # Keywords: cuisine and restriction as neutral
            rdk_keyword_ids: List[int] = []
            if cuisine:
                kid = get_or_create_keyword(conn, kw_cache, cuisine, "cuisine", "neutral")
                bump_dish_keyword(conn, dish_id, kid, 1)
                rdk_keyword_ids.append(kid)
            if restriction:
                kid = get_or_create_keyword(conn, kw_cache, restriction, "restriction", "neutral")
                bump_dish_keyword(conn, dish_id, kid, 1)
                rdk_keyword_ids.append(kid)

            # Sentiment keywords
            sent = item.get("sentiment") or {}
            pos = sent.get("positive") or []
            neg = sent.get("negative") or []
            # Deduplicate tokens per review-dish
            seen: Set[Tuple[str, str, str]] = set()
            for tok in pos:
                t = str(tok).strip()
                if not t:
                    continue
                cat, senti = categorize_keyword(t, "positive")
                key = (t, cat, senti)
                if key in seen:
                    continue
                seen.add(key)
                kid = get_or_create_keyword(conn, kw_cache, t, cat, senti)
                bump_dish_keyword(conn, dish_id, kid, 1)
                rdk_keyword_ids.append(kid)
            for tok in neg:
                t = str(tok).strip()
                if not t:
                    continue
                cat, senti = categorize_keyword(t, "negative")
                key = (t, cat, senti)
                if key in seen:
                    continue
                seen.add(key)
                kid = get_or_create_keyword(conn, kw_cache, t, cat, senti)
                bump_dish_keyword(conn, dish_id, kid, 1)
                rdk_keyword_ids.append(kid)

            insert_review_dish_keywords(conn, rdid, rdk_keyword_ids)
        processed_rows += 1

    if offset is None:
        eff_offset = 0
    else:
        eff_offset = offset
    logger.info(
        "Slice start=%d, limit=%s -> fetched=%d rows; processed=%d rows with non-empty extractions.",
        eff_offset,
        str(limit) if limit is not None else "ALL",
        total_rows,
        processed_rows,
    )

    # Recompute aggregate scores and restaurant metadata
    recompute_dish_scores(conn)
    recompute_restaurant_stats(conn)


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
        process(
            conn,
            source_type_filter=args.source_type,
            limit=args.limit,
            offset=resolved_offset,
            logger=logger,
        )
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
