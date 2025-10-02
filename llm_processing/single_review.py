import os
import argparse
import pandas as pd

from .config import Config
from .logging_setup import setup_logging
from .db import DB
from .processor import process_rows
import json


def run_single(restaurant: str, review: str, source_id: int, source_type: str = "user") -> int:
    # Ensure DB writes are enabled for this run
    os.environ.setdefault("PG_WRITE_DISABLED", "0")
    # Align source_id so that computed source_id = RowNumber(1) + offset
    os.environ["SOURCE_ID_OFFSET"] = str(int(source_id) - 1)

    # Early diagnostics to the log
    try:
        import sys
        print(f"Python exec: {sys.executable}")
        print(f"Python version: {sys.version}")
        print(f"PYTHON_EXEC_USED env: {os.environ.get('PYTHON_EXEC_USED','')}\nPYTHONPATH: {os.environ.get('PYTHONPATH','')}")
        # Show first few sys.path entries
        for i, p in enumerate(sys.path[:5]):
            print(f"sys.path[{i}]: {p}")
    except Exception:
        pass

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

    # If extraction returned an empty array (common for short/generic text) and this is a user
    # review with known dish hints, upsert a minimal record using the hint so users see their
    # submission reflected.
    try:
        if source_type == "user":
            hint_dish_id = os.environ.get("HINT_DISH_ID")
            hint_res_id = os.environ.get("HINT_RES_ID")
            hint_dish = os.environ.get("HINT_DISH_NAME", "").strip()
            # Determine if extracted JSON is empty
            is_empty_extract = True
            if isinstance(results, list) and results:
                ej = results[0].get("Extracted JSON", "")
                try:
                    arr = json.loads(ej) if isinstance(ej, str) and ej.strip() else []
                    is_empty_extract = not (isinstance(arr, list) and len(arr) > 0)
                except Exception:
                    is_empty_extract = True
            if is_empty_extract and (hint_dish or hint_dish_id):
                payload = [{
                    "restaurant": restaurant,
                    "dish": hint_dish or f"dish_id:{hint_dish_id}",
                    "cuisine": None,
                    "restriction": None,
                    "sentiment": {"positive": [], "negative": []},
                    "_hints": {
                        "dish_id": int(hint_dish_id) if hint_dish_id else None,
                        "res_id": int(hint_res_id) if hint_res_id else None,
                    }
                }]
                row = {
                    "Row Number": 1,
                    "Restaurant Name": restaurant,
                    "Review Text": review,
                    "Status": "Success",
                    "Extracted JSON": json.dumps(payload, ensure_ascii=False),
                }
                db.upsert_review_extracts([row], source_type=source_type)
                return 1
    except Exception as _e:
        logger.warning("hint-based fallback insert failed: %s", _e)

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
