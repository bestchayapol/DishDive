import argparse
import logging
import os
import sys
from typing import List, Tuple
import pathlib

import pandas as pd

# Ensure project root is on sys.path so we can import llm_processing when running this file directly
# This file lives in scripts/llm_related/, so project root is two levels up.
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Reuse project config and DB helpers
from llm_processing.config import Config
from llm_processing.db import DB


def parse_pairs(pairs: List[str]) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    for p in pairs:
        if ":" not in p:
            raise ValueError(f"Invalid --pair value '{p}'. Expected format: path:offset")
        path, off = p.split(":", 1)
        path = path.strip().strip('"')
        try:
            offset = int(off)
        except ValueError:
            raise ValueError(f"Invalid offset in pair '{p}'. Offset must be integer.")
        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV not found: {path}")
        out.append((path, offset))
    return out


def load_results_with_offset(path: str, offset: int) -> List[dict]:
    df = pd.read_csv(path, keep_default_na=False)
    results: List[dict] = []
    for _, row in df.iterrows():
        r = dict(row)
        try:
            rn = int(r.get("Row Number"))
        except Exception:
            # Skip rows without a usable Row Number
            continue
        r["Row Number"] = rn + offset
        # Normalize Status default to Success if missing/blank
        if not r.get("Status"):
            r["Status"] = "Success"
        # Ensure Extracted JSON is a string
        ex = r.get("Extracted JSON")
        if ex is None:
            r["Extracted JSON"] = "[]"
        results.append(r)
    return results


def chunked(seq: List[dict], size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def main():
    ap = argparse.ArgumentParser(description="Import processed review CSVs into Postgres with row-number offsets.")
    ap.add_argument(
        "--pair",
        action="append",
        required=True,
        help="CSV path and offset in the form path:offset. Repeat for multiple files.",
    )
    ap.add_argument(
        "--source-type",
        default="web",
        help="Value for source_type column (default: web)",
    )
    ap.add_argument(
        "--batch",
        type=int,
        default=1000,
        help="Batch size for DB upserts (default: 1000)",
    )
    ap.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Logging level (default: INFO)",
    )
    args = ap.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format="[%(levelname)s] %(message)s")
    logger = logging.getLogger("csv-import")

    pairs = parse_pairs(args.pair)

    # Read env for DB config; require PG_WRITE_DISABLED to be false to write
    cfg = Config()
    db = DB(cfg, logger)

    if cfg.pg_write_disabled:
        logger.error("PG_WRITE_DISABLED is true; set PG_WRITE_DISABLED=0 or false to enable writes.")
        return 2

    db.ensure_table()

    total_read = 0
    total_inserted = 0

    for path, offset in pairs:
        logger.info("Loading %s with offset %+d", path, offset)
        results = load_results_with_offset(path, offset)
        total_read += len(results)
        logger.info("Loaded %d rows from %s", len(results), path)
        for chunk in chunked(results, args.batch):
            inserted = db.upsert_review_extracts(chunk, source_type=args.source_type)
            total_inserted += inserted
            logger.info("Inserted %d rows (cumulative %d)", inserted, total_inserted)

    logger.info("Done. Read %d rows across %d files; inserted %d rows after filtering.", total_read, len(pairs), total_inserted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
