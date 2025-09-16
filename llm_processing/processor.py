import os
import json
import ast
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

from .config import Config
from .utils import (
    should_skip_review,
    extract_json,
    is_balanced_json,
    has_unterminated_string,
    fix_json_keys,
    clean_json_string,
    build_fallback_entries,
    TTLCache,
)
from .db import DB

def process_single_row(idx, row, cache: TTLCache, prefilter_enabled: bool, logger):
    input_data = {
        "restaurant": str(getattr(row, "restaurant_name", "")),
        "review": str(getattr(row, "review_text", ""))
    }
    if prefilter_enabled and should_skip_review(input_data["review"], input_data["restaurant"]):
        return {
            "Row Number": idx + 1,
            "Restaurant Name": input_data["restaurant"],
            "Review Text": input_data["review"],
            "Status": "Success",
            "Extracted JSON": "[]",
            "Error Message": "Skipped by prefilter",
        }

    cache_key = f"{input_data['restaurant']}||{input_data['review']}"
    cached = cache.get(cache_key)
    if cached is not None:
        return {
            "Row Number": idx + 1,
            "Restaurant Name": input_data["restaurant"],
            "Review Text": input_data["review"],
            "Status": "Success",
            "Extracted JSON": cached,
            "Error Message": "cache hit",
        }

    from .utils import extract_dishes_rule_based
    dishes = extract_dishes_rule_based(input_data["review"])
    if not dishes:
        fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
        return {
            "Row Number": idx + 1,
            "Restaurant Name": input_data["restaurant"],
            "Review Text": input_data["review"],
            "Status": "Success",
            "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
            "Error Message": "fallback: no dishes found",
        }

    from .llm import gpt35_extract
    results = []
    try:
        raw = gpt35_extract(input_data["restaurant"], input_data["review"])
    except Exception as e:
        logger.warning("OpenAI call failed for row %s: %s", idx + 1, e)
        raw = ""
    json_str = extract_json(raw)
    if json_str and is_balanced_json(json_str):
        try:
            obj = json.loads(json_str)
            if isinstance(obj, list):
                for o in obj:
                    if isinstance(o, dict):
                        results.append(o)
            elif isinstance(obj, dict):
                results.append(obj)
        except Exception as e:
            logger.warning("JSON parse failed for row %s: %s", idx + 1, e)
    if not results:
        fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
        return {
            "Row Number": idx + 1,
            "Restaurant Name": input_data["restaurant"],
            "Review Text": input_data["review"],
            "Status": "Success",
            "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
            "Error Message": "fallback: llm failed or empty output",
        }
    res = {
        "Row Number": idx + 1,
        "Restaurant Name": input_data["restaurant"],
        "Review Text": input_data["review"],
        "Status": "Success",
        "Extracted JSON": json.dumps(results, ensure_ascii=False, indent=2),
        "Error Message": "",
    }
    cache.set(cache_key, res["Extracted JSON"])
    return res
    input_data = {
        "restaurant": str(getattr(row, "restaurant_name", "")),
        "review": str(getattr(row, "review_text", ""))
    }
    if prefilter_enabled and should_skip_review(input_data["review"], input_data["restaurant"]):
        return {
            "Row Number": idx + 1,
            "Restaurant Name": input_data["restaurant"],
            "Review Text": input_data["review"],
            "Status": "Success",
            "Extracted JSON": "[]",
            "Error Message": "Skipped by prefilter",
        }

    cache_key = f"{input_data['restaurant']}||{input_data['review']}"
    cached = cache.get(cache_key)
    if cached is not None:
        return {
            "Row Number": idx + 1,
            "Restaurant Name": input_data["restaurant"],
            "Review Text": input_data["review"],
            "Status": "Success",
            "Extracted JSON": cached,
            "Error Message": "cache hit",
        }

    # --- Hybrid pipeline: rule-based dish extraction, LLM for details ---
    from .utils import extract_dishes_rule_based
    dishes = extract_dishes_rule_based(input_data["review"])
    if not dishes:
        fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
        return {
            "Row Number": idx + 1,
            "Restaurant Name": input_data["restaurant"],
            "Review Text": input_data["review"],
            "Status": "Success",
            "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
            "Error Message": "fallback: no dishes found",
        }

        from .llm import gpt35_extract
        results = []
        # Use GPT-3.5 for full extraction (single call per review)
        try:
            raw = gpt35_extract(input_data["restaurant"], input_data["review"])
            json_str = extract_json(raw)
            if json_str and is_balanced_json(json_str):
                try:
                    obj = json.loads(json_str)
                    if isinstance(obj, list):
                        for o in obj:
                            if isinstance(o, dict):
                                results.append(o)
                    elif isinstance(obj, dict):
                        results.append(obj)
                except Exception:
                    pass
        except Exception:
            pass
    if not results:
        fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
        return {
            "Row Number": idx + 1,
            "Restaurant Name": input_data["restaurant"],
            "Review Text": input_data["review"],
            "Status": "Success",
            "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
            "Error Message": "fallback: llm failed for all dishes",
        }
    res = {
        "Row Number": idx + 1,
        "Restaurant Name": input_data["restaurant"],
        "Review Text": input_data["review"],
        "Status": "Success",
        "Extracted JSON": json.dumps(results, ensure_ascii=False, indent=2),
        "Error Message": "",
    }
    cache.set(cache_key, res["Extracted JSON"])
    return res




def process_rows(df: pd.DataFrame, cfg: Config, db: DB, logger):
    processed_indices = set()
    results: List[dict] = []
    buffer: List[dict] = []
    error_log: List[dict] = []
    cache = TTLCache(max_size=cfg.ollama_cache_max, ttl_sec=cfg.ollama_cache_ttl_sec)

    # Resolve output paths
    default_output_name = "processed_reviews.csv"
    output_path = cfg.output_csv if cfg.output_csv else os.path.join(cfg.output_dir, default_output_name)
    checkpoint_path = os.path.join(cfg.output_dir, "processed_reviews_checkpoint.csv")
    data_extract_path = os.path.join(cfg.output_dir, "processed_reviews_data_extract.csv")

    # Ensure output directories exist
    os.makedirs(cfg.output_dir, exist_ok=True)
    out_dirname = os.path.dirname(output_path)
    if out_dirname:
        os.makedirs(out_dirname, exist_ok=True)

    if cfg.write_checkpoint and os.path.exists(checkpoint_path):
        checkpoint_df = pd.read_csv(checkpoint_path, keep_default_na=False)
        processed_indices = set(checkpoint_df["Row Number"] - 1)
        results = checkpoint_df.to_dict(orient="records")
        logger.info("Resuming from checkpoint, %s rows already processed.", len(processed_indices))

    rows_to_process = [
        (idx, row) for idx, row in enumerate(df.itertuples(index=False))
        if idx not in processed_indices
    ]

    batch_size = cfg.batch_size
    batch_min = max(1, batch_size // 2)
    batch_max = max(batch_size, 4)

    logger.info("Starting processing %s restaurants...", len(rows_to_process))
    overall_start = time.time()
    start_idx = 0
    total_batches = 0
    total_rows = 0
    while start_idx < len(rows_to_process):
        batch = rows_to_process[start_idx:start_idx+batch_size]
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=cfg.max_workers) as executor:
            futures = [
                executor.submit(
                        process_single_row, idx, row, cache, cfg.prefilter_enabled, logger
                ) for idx, row in batch
            ]
            for fut in as_completed(futures):
                res = fut.result()
                results.append(res)
                buffer.append(res)
                if len(buffer) >= 1000 and db.writes_enabled():
                    try:
                        db.upsert_review_extracts(buffer)
                        buffer = []
                    except Exception as e:
                        logger.warning("Failed DB upsert at checkpoint: %s", e)

        elapsed = time.time() - t0
        logger.info("Batch processed in %.2fs (size=%s)", elapsed, len(batch))
        total_batches += 1
        total_rows += len(batch)

        # Checkpoint to CSV (optional)
        if cfg.write_checkpoint:
            pd.DataFrame(results).to_csv(checkpoint_path, index=False)
        # Adjust next batch size
        if elapsed < max(1.0, 0.5 * cfg.target_batch_sec) and batch_size < batch_max:
            batch_size = min(batch_max, max(batch_size + 1, int(batch_size * 1.25)))
        elif elapsed > 1.5 * cfg.target_batch_sec and batch_size > batch_min:
            batch_size = max(batch_min, min(batch_size - 1, int(batch_size * 0.8)))

        if cfg.cooldown_sec > 0:
            time.sleep(cfg.cooldown_sec)

        start_idx += len(batch)

    overall_elapsed = time.time() - overall_start
    avg_per_row = overall_elapsed / total_rows if total_rows else 0
    projected_100k = avg_per_row * 100000 if avg_per_row else 0
    logger.info("=== Timing summary ===")
    logger.info("Total time: %.2fs for %d rows", overall_elapsed, total_rows)
    logger.info("Average per row: %.3fs", avg_per_row)
    logger.info("Projected for 100,000 rows: %.1f hours (%.1f minutes)", projected_100k/3600, projected_100k/60)

    # final DB flush
    if buffer and db.writes_enabled():
        try:
            db.upsert_review_extracts(buffer)
        except Exception as e:
            logger.warning("Failed final DB upsert: %s", e)

    # final export (single output file)
    pd.DataFrame(results).to_csv(output_path, index=False)
    # data_extract shaped CSV (optional)
    if cfg.write_data_extract:
        _write_data_extract_csv_from_results(results, data_extract_path)
        logger.info("Processing complete. Output: %s | data_extract: %s", output_path, data_extract_path)
    else:
        logger.info("Processing complete. Output: %s", output_path)
    return results


def _write_data_extract_csv_from_results(results: list, out_csv: str):
    out_rows = []
    for r in results:
        ex = r.get("Extracted JSON")
        arr = []
        if isinstance(ex, str) and ex.strip():
            try:
                arr = json.loads(ex)
                if not isinstance(arr, list):
                    arr = []
            except Exception:
                arr = []
        if not arr:
            rest = r.get("Restaurant Name") or ""
            review = r.get("Review Text") or ""
            arr = build_fallback_entries(rest, review)
        out_rows.append({"data_extract": json.dumps({"data_extract": arr}, ensure_ascii=False)})
    pd.DataFrame(out_rows).to_csv(out_csv, index=False)
