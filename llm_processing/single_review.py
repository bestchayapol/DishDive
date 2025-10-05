import os
import argparse
import pandas as pd

from .config import Config
from .logging_setup import setup_logging
from .db import DB
from .processor import process_rows
from .normalize_incremental import normalize_single
from .utils import is_valid_dish_name, build_fallback_entries
import json


def run_single(restaurant: str, review: str, source_id: int, source_type: str = "user") -> int:
    # Ensure DB writes are enabled for this run
    os.environ.setdefault("PG_WRITE_DISABLED", "0")
    # Force the exact source_id instead of relying on offset math
    os.environ["FORCE_SOURCE_ID"] = str(int(source_id))
    # Remove any stale offset variable to avoid confusion
    if "SOURCE_ID_OFFSET" in os.environ:
        os.environ.pop("SOURCE_ID_OFFSET", None)

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

    # Reuse the batch processor; it will call DB.upsert_review_extracts internally (only if at least one valid dish)
    results = process_rows(df, cfg, db, logger)

    # If extraction returned an empty array (common for short/generic text) and this is a user
    # review with known dish hints, upsert a minimal record using the hint so users see their
    # submission reflected.
    # If no valid dish objects were persisted (buffer gating) but we have hints, insert a fallback row now
    try:
        hint_dish_id = os.environ.get("HINT_DISH_ID")
        hint_res_id = os.environ.get("HINT_RES_ID")
        hint_dish = os.environ.get("HINT_DISH_NAME", "").strip()
        need_fallback = False
        if isinstance(results, list) and results:
            ej = results[0].get("Extracted JSON", "")
            try:
                arr = json.loads(ej) if isinstance(ej, str) and ej.strip() else []
            except Exception:
                arr = []
            # Determine if any object has a valid dish name
            has_valid = False
            for o in arr:
                if isinstance(o, dict) and is_valid_dish_name(str(o.get("dish",""))):
                    has_valid = True
                    break
            if not has_valid:
                need_fallback = True
        else:
            need_fallback = True
        if source_type == "user" and need_fallback and (hint_dish or hint_dish_id):
            # Reuse build_fallback_entries so we get sentiment inference
            payload = build_fallback_entries(restaurant, review)
            # Ensure we override dish name if explicit hint provided
            if payload and (hint_dish or hint_dish_id):
                payload[0]["dish"] = hint_dish or f"dish_id:{hint_dish_id}"
                if "_hints" not in payload[0]:
                    payload[0]["_hints"] = {}
                payload[0]["_hints"]["dish_id"] = int(hint_dish_id) if hint_dish_id else None
                payload[0]["_hints"]["res_id"] = int(hint_res_id) if hint_res_id else None
            row = {
                "Row Number": 1,
                "Restaurant Name": restaurant,
                "Review Text": review,
                "Status": "Success",
                "Extracted JSON": json.dumps(payload, ensure_ascii=False),
            }
            db.upsert_review_extracts([row], source_type=source_type)
            logger.info("Inserted hint-based fallback extract (with inferred sentiment) for source_id=%s", source_id)
    except Exception as _e:
        logger.warning("hint-based fallback evaluation failed: %s", _e)

    # Return number of rows attempted (1) if successful insertion else 0
    # After writing extract, optionally normalize immediately
    auto_norm = os.environ.get("AUTO_NORMALIZE", "1").strip().lower() in ("1","true","yes")
    if auto_norm:
        try:
            normalize_single(source_id, source_type)
        except Exception as e:
            logger.warning("incremental normalization failed: %s", e)
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
