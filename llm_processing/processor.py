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


def process_single_row(idx, row, chain, cache: TTLCache, prefilter_enabled: bool, logger):
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

    try:
        response = chain.invoke(input_data)
        if isinstance(response, dict):
            raw = response.get("text", "").strip()
        elif isinstance(response, str):
            raw = response.strip()
        else:
            raw = ""

        if not raw:
            fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                "Error Message": "fallback: empty output",
            }

        json_str = extract_json(raw)
        if not json_str:
            fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                "Error Message": "fallback: no json found",
            }

        if not is_balanced_json(json_str):
            fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                "Error Message": "fallback: unbalanced json",
            }
        if has_unterminated_string(json_str):
            fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                "Error Message": "fallback: unterminated string",
            }

        try:
            try:
                json_result = json.loads(json_str)
            except json.JSONDecodeError:
                fixed_json_str = fix_json_keys(json_str)
                fixed_json_str = clean_json_string(fixed_json_str)
                try:
                    json_result = json.loads(fixed_json_str)
                except Exception:
                    json_result = ast.literal_eval(fixed_json_str)

            def is_valid_entry(obj):
                try:
                    if not isinstance(obj, dict):
                        return False
                    d = obj.get("dish", None) or obj.get("เมนู", None) or obj.get("ชื่อเมนู", None)
                except AttributeError:
                    return False
                return isinstance(d, str) and d.strip() != ""

            if isinstance(json_result, list):
                normalized = [o for o in json_result if isinstance(o, dict) and is_valid_entry(o)]
            elif isinstance(json_result, dict):
                normalized = [json_result] if is_valid_entry(json_result) else []
            else:
                normalized = []

            if not normalized:
                fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
                res = {
                    "Row Number": idx + 1,
                    "Restaurant Name": input_data["restaurant"],
                    "Review Text": input_data["review"],
                    "Status": "Success",
                    "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                    "Error Message": "",
                }
                cache.set(cache_key, res["Extracted JSON"])  # cache fallback too
                return res

            res = {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(normalized, ensure_ascii=False, indent=2),
                "Error Message": "",
            }
            cache.set(cache_key, res["Extracted JSON"])  # cache good output
            return res
        except Exception as e:
            fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
                "Error Message": f"fallback: exception ({str(e)})",
            }
    except Exception as e:
        fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
        return {
            "Row Number": idx + 1,
            "Restaurant Name": input_data["restaurant"],
            "Review Text": input_data["review"],
            "Status": "Success",
            "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
            "Error Message": f"fallback: exception ({str(e)})",
        }


def process_rows(df: pd.DataFrame, cfg: Config, chain, db: DB, logger):
    processed_indices = set()
    results: List[dict] = []
    buffer: List[dict] = []
    error_log: List[dict] = []
    cache = TTLCache(max_size=cfg.ollama_cache_max, ttl_sec=cfg.ollama_cache_ttl_sec)

    checkpoint_path = os.path.join(cfg.output_dir, "processed_bangkok_restaurant_reviews_checkpoint_2000.csv")
    output_path = os.path.join(cfg.output_dir, "processed_bangkok_restaurant_reviews_2000.csv")
    data_extract_path = os.path.join(cfg.output_dir, "processed_bangkok_restaurant_reviews_data_extract_2000.csv")

    os.makedirs(cfg.output_dir, exist_ok=True)

    if os.path.exists(checkpoint_path):
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
    start_idx = 0
    while start_idx < len(rows_to_process):
        batch = rows_to_process[start_idx:start_idx+batch_size]
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=cfg.max_workers) as executor:
            futures = [
                executor.submit(
                    process_single_row, idx, row, chain, cache, cfg.prefilter_enabled, logger
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
        logger.info("Batch processed in %.2fs (size=%s)", elapsed, batch_size)

        # Checkpoint to CSV
        pd.DataFrame(results).to_csv(checkpoint_path, index=False)
        # Adjust next batch size
        if elapsed < max(1.0, 0.5 * cfg.target_batch_sec) and batch_size < batch_max:
            batch_size = min(batch_max, max(batch_size + 1, int(batch_size * 1.25)))
        elif elapsed > 1.5 * cfg.target_batch_sec and batch_size > batch_min:
            batch_size = max(batch_min, min(batch_size - 1, int(batch_size * 0.8)))

        if cfg.cooldown_sec > 0:
            time.sleep(cfg.cooldown_sec)

        start_idx += len(batch)

    # final DB flush
    if buffer and db.writes_enabled():
        try:
            db.upsert_review_extracts(buffer)
        except Exception as e:
            logger.warning("Failed final DB upsert: %s", e)

    # final export
    pd.DataFrame(results).to_csv(output_path, index=False)
    # data_extract shaped CSV
    _write_data_extract_csv_from_results(results, data_extract_path)

    logger.info("Processing complete. Output: %s | data_extract: %s", output_path, data_extract_path)
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
