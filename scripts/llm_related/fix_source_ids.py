import argparse
import logging
import os
import sys
import pathlib
from typing import Optional, Tuple, List

import psycopg2

# Ensure project root in path for config reuse (this script is in scripts/llm_related -> root is two levels up)
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_processing.config import Config  # type: ignore

# Added utilities for new flags


def parse_rev_range(range_str: str) -> Tuple[int, int]:
    try:
        start_s, end_s = range_str.split("-", 1)
        start, end = int(start_s), int(end_s)
    except ValueError:
        raise argparse.ArgumentTypeError("--rev-range must be in form START-END (both inclusive integers)")
    if start > end:
        raise argparse.ArgumentTypeError("--rev-range start must be <= end")
    return start, end


def adjust_source_ids(
    conn,
    add: int,
    source_type: Optional[str],
    min_source_id: Optional[int],
    max_source_id: Optional[int],
    min_rev_ext_id: Optional[int],
    max_rev_ext_id: Optional[int],
    dry_run: bool,
    verbose: bool,
) -> int:
    """Bulk add a value to review_extracts.source_id with optional filters.

    Filters (all optional):
      - source_type: filter by review_extracts.source_type
      - min_source_id / max_source_id: constrain CURRENT source_id range BEFORE adjustment
      - min_rev_ext_id / max_rev_ext_id: constrain by rev_ext_id primary key range
    """
    where_clauses: List[str] = []
    params: List[object] = []
    if source_type:
        where_clauses.append("LOWER(source_type) = LOWER(%s)")
        params.append(source_type)
    if min_source_id is not None:
        where_clauses.append("source_id >= %s")
        params.append(min_source_id)
    if max_source_id is not None:
        where_clauses.append("source_id <= %s")
        params.append(max_source_id)
    if min_rev_ext_id is not None:
        where_clauses.append("rev_ext_id >= %s")
        params.append(min_rev_ext_id)
    if max_rev_ext_id is not None:
        where_clauses.append("rev_ext_id <= %s")
        params.append(max_rev_ext_id)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM review_extracts {where_sql}", params)
        total = cur.fetchone()[0]

    if total == 0:
        logging.warning("No rows match filters; nothing to do.")
        return 0

    if verbose:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT rev_ext_id, source_id FROM review_extracts {where_sql} ORDER BY rev_ext_id LIMIT 20",
                params,
            )
            sample = cur.fetchall()
        logging.info("Sample BEFORE update (rev_ext_id, source_id): %s", sample)

    logging.info(
        "Matched %d rows in review_extracts; applying increment %d to source_id (dry_run=%s)",
        total,
        add,
        dry_run,
    )

    if dry_run:
        logging.info("Dry run complete; no changes written.")
        return total

    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE review_extracts SET source_id = source_id + %s {where_sql}",
            [add] + params,
        )

    if verbose:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT rev_ext_id, source_id FROM review_extracts {where_sql} ORDER BY rev_ext_id LIMIT 20",
                params,
            )
            after_sample = cur.fetchall()
        logging.info("Sample AFTER update (rev_ext_id, source_id): %s", after_sample)

    conn.commit()
    logging.info("Updated %d rows.")
    return total


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Bulk adjust review_extracts.source_id values. You can select rows by rev_ext_id range (use --rev-min/--rev-max or --rev-range) and/or by current source_id range."
        )
    )
    ap.add_argument("--add", type=int, required=True, help="Value to add (can be negative) to source_id")
    ap.add_argument("--source-type", default=None, help="Filter by review_extracts.source_type")
    # Source ID filters
    ap.add_argument("--min-id", dest="min_source_id", type=int, default=None, help="Minimum CURRENT source_id (inclusive)")
    ap.add_argument("--max-id", dest="max_source_id", type=int, default=None, help="Maximum CURRENT source_id (inclusive)")
    # rev_ext_id filters
    ap.add_argument("--rev-min", dest="min_rev_ext_id", type=int, default=None, help="Minimum rev_ext_id (inclusive)")
    ap.add_argument("--rev-max", dest="max_rev_ext_id", type=int, default=None, help="Maximum rev_ext_id (inclusive)")
    ap.add_argument(
        "--rev-range",
        type=parse_rev_range,
        default=None,
        help="Shorthand for rev_ext_id range START-END (inclusive). Overrides --rev-min/--rev-max when present.",
    )
    ap.add_argument("--dry-run", action="store_true", help="Show how many rows would change without applying")
    ap.add_argument("--verbose", action="store_true", help="Print sample rows before/after update")
    ap.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    args = ap.parse_args()

    if args.rev_range:
        args.min_rev_ext_id, args.max_rev_ext_id = args.rev_range

    logging.basicConfig(level=args.log_level.upper(), format="[%(levelname)s] %(message)s")

    if (args.min_source_id is not None or args.max_source_id is not None) and (args.min_rev_ext_id is None and args.max_rev_ext_id is None):
        logging.warning("Filtering by source_id range only. If you intended rev_ext_id filtering, use --rev-min/--rev-max or --rev-range.")

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
        adjust_source_ids(
            conn,
            add=args.add,
            source_type=args.source_type,
            min_source_id=args.min_source_id,
            max_source_id=args.max_source_id,
            min_rev_ext_id=args.min_rev_ext_id,
            max_rev_ext_id=args.max_rev_ext_id,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
