import argparse
import csv
import logging
import os
import pathlib
import sys
from typing import Dict, Tuple, List, Set

import psycopg2

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_processing.config import Config  # noqa: E402


def load_dish_alias_csv(path: pathlib.Path) -> List[Tuple[str, str, int, int]]:
    """Return list of (canonical, member, proposed, accept)."""
    out = []
    with path.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"cluster_id", "canonical_dish", "member_dish", "proposed", "accept"}
        missing = required - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"dish alias CSV missing columns: {missing}")
        for row in r:
            try:
                out.append((row["canonical_dish"].strip(), row["member_dish"].strip(), int(row.get("proposed", 1)), int(row.get("accept", 0))))
            except Exception:
                continue
    return out


def load_keyword_alias_csv(path: pathlib.Path) -> List[Tuple[str, str, str, int, int]]:
    out = []
    with path.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"cluster_id", "category", "canonical_keyword", "member_keyword", "proposed", "accept"}
        missing = required - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"keyword alias CSV missing columns: {missing}")
        for row in r:
            try:
                out.append((row["category"].strip(), row["canonical_keyword"].strip(), row["member_keyword"].strip(), int(row.get("proposed", 1)), int(row.get("accept", 0))))
            except Exception:
                continue
    return out


def load_restaurant_location_csv(path: pathlib.Path) -> List[Tuple[str, str, int, int]]:
    out = []
    with path.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        required = {"cluster_id", "canonical_restaurant", "raw_restaurant_name", "location_name", "proposed", "accept"}
        missing = required - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"restaurant location CSV missing columns: {missing}")
        for row in r:
            try:
                out.append((row["canonical_restaurant"].strip(), row["raw_restaurant_name"].strip(), int(row.get("proposed", 1)), int(row.get("accept", 0))))
            except Exception:
                continue
    return out


def build_name_id_maps(conn):
    dishes: Dict[str, int] = {}
    keywords: Dict[Tuple[str, str], int] = {}
    restaurants: Dict[str, int] = {}
    restaurants_by_id: Dict[int, str] = {}
    with conn.cursor() as cur:
        cur.execute("SELECT dish_id, dish_name FROM dishes")
        for did, name in cur.fetchall():
            dishes[str(name).strip()] = int(did)
        cur.execute("SELECT keyword_id, keyword, category FROM keywords")
        for kid, kw, cat in cur.fetchall():
            keywords[(str(kw).strip(), str(cat).strip())] = int(kid)
        cur.execute("SELECT res_id, res_name FROM restaurants")
        for rid, name in cur.fetchall():
            n = str(name).strip()
            restaurants[n] = int(rid)
            restaurants_by_id[int(rid)] = n
    return dishes, keywords, restaurants, restaurants_by_id


def upsert_dish_aliases(conn, dish_aliases: List[Tuple[int, str]], dry_run: bool, logger):
    if not dish_aliases:
        return 0
    with conn.cursor() as cur:
        for dish_id, alt_name in dish_aliases:
            if dry_run:
                logger.info("DRY RUN dish_alias (%s -> %s)", dish_id, alt_name)
                continue
            cur.execute(
                "INSERT INTO dish_aliases (dish_id, alt_name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (dish_id, alt_name),
            )
    if not dry_run:
        conn.commit()
    return len(dish_aliases)


def upsert_keyword_aliases(conn, keyword_aliases: List[Tuple[int, str]], dry_run: bool, logger):
    if not keyword_aliases:
        return 0
    with conn.cursor() as cur:
        for keyword_id, alt_word in keyword_aliases:
            if dry_run:
                logger.info("DRY RUN keyword_alias (%s -> %s)", keyword_id, alt_word)
                continue
            cur.execute(
                "INSERT INTO keyword_aliases (keyword_id, alt_word) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (keyword_id, alt_word),
            )
    if not dry_run:
        conn.commit()
    return len(keyword_aliases)


def upsert_restaurant_locations(conn, rest_locs: List[Tuple[int, str]], dry_run: bool, logger):
    if not rest_locs:
        return 0
    with conn.cursor() as cur:
        for res_id, location_name in rest_locs:
            if not location_name:
                continue  # skip blank (canonical rows without location segment)
            # Avoid duplicates: check existence on (res_id, location_name)
            cur.execute(
                "SELECT 1 FROM restaurant_locations WHERE res_id=%s AND location_name=%s LIMIT 1",
                (res_id, location_name),
            )
            exists = cur.fetchone() is not None
            if exists:
                logger.debug("Skip existing restaurant_location (%s, %s)", res_id, location_name)
                continue
            if dry_run:
                logger.info("DRY RUN restaurant_location INSERT (%s -> %s)", res_id, location_name)
                continue
            cur.execute(
                "INSERT INTO restaurant_locations (res_id, location_name, address, latitude, longitude) VALUES (%s, %s, '', 0, 0)",
                (res_id, location_name),
            )
    if not dry_run:
        conn.commit()
    return len(rest_locs)


def main():
    ap = argparse.ArgumentParser(description="Apply curated alias CSVs into dish_aliases, keyword_aliases, restaurant_locations")
    ap.add_argument("--dish-csv", default="alias_candidates/alias_dish_candidates.csv", help="Path to curated dish alias CSV")
    ap.add_argument("--keyword-csv", default="alias_candidates/alias_keyword_candidates.csv", help="Path to curated keyword alias CSV")
    ap.add_argument("--restaurant-csv", default="alias_candidates/restaurant_location_candidates.csv", help="Path to curated restaurant location CSV")
    ap.add_argument("--accept-only", action="store_true", help="Only apply rows where accept=1 (default)")
    ap.add_argument("--include-rejected", action="store_true", help="Also apply rows with accept=0 (overrides accept-only)")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without writing to DB")
    ap.add_argument("--no-default-locations", action="store_true", help="Do not create a default location row for restaurants without any locations")
    ap.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    args = ap.parse_args()

    # accept_only logic
    accept_only = not args.include_rejected

    logging.basicConfig(level=args.log_level.upper(), format="[%(levelname)s] %(message)s")
    logger = logging.getLogger("apply_alias")

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
        dish_alias_rows = load_dish_alias_csv(pathlib.Path(args.dish_csv))
        keyword_alias_rows = load_keyword_alias_csv(pathlib.Path(args.keyword_csv))
        rest_location_rows = load_restaurant_location_csv(pathlib.Path(args.restaurant_csv))
        
        dishes_map, keywords_map, restaurants_map, restaurants_by_id = build_name_id_maps(conn)
        logger.info("Loaded name->id maps: dishes=%d keywords=%d restaurants=%d", len(dishes_map), len(keywords_map), len(restaurants_map))

        dish_alias_inserts: List[Tuple[int, str]] = []
        keyword_alias_inserts: List[Tuple[int, str]] = []
        rest_location_inserts: List[Tuple[int, str]] = []

        # --- Dishes ---
        for canonical, member, proposed, accept in dish_alias_rows:
            if accept_only and not accept:
                continue
            if canonical == member:
                continue  # skip canonical identity rows
            dish_id = dishes_map.get(canonical)
            if not dish_id:
                continue
            dish_alias_inserts.append((dish_id, member))

        # --- Keywords ---
        for category, canonical_kw, member_kw, proposed, accept in keyword_alias_rows:
            if accept_only and not accept:
                continue
            if canonical_kw == member_kw:
                continue
            kid = keywords_map.get((canonical_kw, category))
            if not kid:
                continue
            keyword_alias_inserts.append((kid, member_kw))

        # --- Restaurant Locations ---
        # We treat raw_restaurant_name rows: if different from canonical, attempt to extract location token
        # The generator already placed a location_name column; we just use canonical vs raw difference.
        with open(args.restaurant_csv, encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    accept = int(row.get("accept", 0))
                except Exception:
                    accept = 0
                if accept_only and not accept:
                    continue
                canonical = (row.get("canonical_restaurant") or "").strip()
                raw = (row.get("raw_restaurant_name") or "").strip()
                location_name = (row.get("location_name") or "").strip()
                if not location_name:
                    continue
                rid = restaurants_map.get(canonical)
                if not rid:
                    continue
                rest_location_inserts.append((rid, location_name))

        # Add a default location for any restaurant that currently has zero locations
        if not args.no_default_locations:
            with conn.cursor() as cur:
                cur.execute("SELECT res_id, COUNT(*) FROM restaurant_locations GROUP BY res_id")
                counts = {int(rid): int(c) for rid, c in cur.fetchall()}
            missing_defaults: List[Tuple[int, str]] = []
            for rid, name in restaurants_by_id.items():
                if counts.get(rid, 0) == 0:
                    missing_defaults.append((rid, name))
            if missing_defaults:
                logger.info("Adding default locations for %d restaurants with no locations", len(missing_defaults))
                rest_location_inserts.extend(missing_defaults)

        logger.info("Prepared inserts: dish_aliases=%d keyword_aliases=%d restaurant_locations=%d", len(dish_alias_inserts), len(keyword_alias_inserts), len(rest_location_inserts))

        di = upsert_dish_aliases(conn, dish_alias_inserts, args.dry_run, logger)
        ki = upsert_keyword_aliases(conn, keyword_alias_inserts, args.dry_run, logger)
        ri = upsert_restaurant_locations(conn, rest_location_inserts, args.dry_run, logger)

        logger.info("Applied: dish_aliases=%d keyword_aliases=%d restaurant_locations=%d", di, ki, ri)
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
