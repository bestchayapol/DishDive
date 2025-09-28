import os
import argparse
import pandas as pd

from .config import Config
from .logging_setup import setup_logging
from .db import DB
from .processor import process_rows


def run_single(restaurant: str, review: str, source_id: int, source_type: str = "user") -> int:
    # Ensure DB writes are enabled for this run
    os.environ.setdefault("PG_WRITE_DISABLED", "0")
    # Align source_id so that computed source_id = RowNumber(1) + offset
    os.environ["SOURCE_ID_OFFSET"] = str(int(source_id) - 1)

    cfg = Config()
    logger = setup_logging(cfg)
    db = DB(cfg, logger)
    db.ensure_table()

    # Build a single-row dataframe compatible with the batch pipeline
    df = pd.DataFrame([
        {"restaurant_name": restaurant, "review_text": review}
    ])

    # Reuse the batch processor; it will call DB.upsert_review_extracts internally
    results = process_rows(df, cfg, db, logger)

    # Return number of rows attempted (1) if successful insertion else 0
    return 1 if results else 0


def main():
    parser = argparse.ArgumentParser(description="Process a single user review through the LLM pipeline")
    parser.add_argument("--restaurant", required=True, help="Restaurant name")
    parser.add_argument("--review", required=True, help="User review text")
    parser.add_argument("--source-id", type=int, required=True, help="Source ID to use for review_extracts (e.g., user_review_id)")
    parser.add_argument("--source-type", default="user", help="Source type label for review_extracts (default: user)")
    args = parser.parse_args()

    # Propagate desired source type to the DB layer by environment (used for logging only)
    os.environ.setdefault("SOURCE_TYPE", args.source_type)

    rc = run_single(args.restaurant, args.review, args.source_id, args.source_type)
    raise SystemExit(0 if rc > 0 else 1)


if __name__ == "__main__":
    main()
