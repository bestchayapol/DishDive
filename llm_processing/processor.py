import os
import json
import ast
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
import logging

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
    is_valid_dish_name,
)
from .db import DB

# Ensure logger is defined
logger = logging.getLogger(__name__)

# Optimize environment variable usage
pg_config = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", ""),
    "database": os.getenv("PG_DATABASE", "postgres"),
}
# Log Postgres configuration
logger.info("Postgres configuration: %s", pg_config)

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

    from .llm import gpt35_extract, _rule_based_extract
    results = []
    try:
        # Implement exponential backoff for retries
        retry_delay = 1.0  # Initial delay in seconds
        max_retries = 5
        for attempt in range(max_retries):
            try:
                raw, tier = gpt35_extract(input_data["restaurant"], input_data["review"])
                break  # Exit loop on success
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning("Retrying in %.2f seconds (attempt %d/%d)", retry_delay, attempt + 1, max_retries)
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("Max retries reached for row %d", idx + 1)
                    raise
    except Exception as e:
        # Unexpected exception (not caught inside gpt35_extract). Log with traceback once per row.
        import traceback
        tb = traceback.format_exc()
        logger.error(
            "gpt35_extract exception row %s (%s): %s\n%s", idx + 1, type(e).__name__, e, tb
        )
        # Attempt rule-based extraction as a smarter fallback instead of generic placeholder
        try:
            rb = _rule_based_extract(input_data["restaurant"], input_data["review"])
        except Exception as rb_e:
            logger.error("rule-based fallback also failed row %s: %s", idx + 1, rb_e)
            rb = []
        if rb:
            return {
                "Row Number": idx + 1,
                "Restaurant Name": input_data["restaurant"],
                "Review Text": input_data["review"],
                "Status": "Success",
                "Extracted JSON": json.dumps(rb, ensure_ascii=False, indent=2),
                "Error Message": f"LLM exception:{type(e).__name__}",
                "Extraction Tier": "rule-based-exception",
            }
        raw = ""  # will fall back to generic build_fallback_entries below
        tier = "error"
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
    # Treat any _error-bearing objects as failure (trigger fallback build)
    if results and any(isinstance(o, dict) and o.get('_error') for o in results):
        results = []
    # Filter invalid dish names (quality/ambience/price leakage)
    if results:
        filtered = []
        for o in results:
            dish = str(o.get("dish",""))
            if is_valid_dish_name(dish):
                filtered.append(o)
        results = filtered

    if not results:
        fb = build_fallback_entries(input_data["restaurant"], input_data["review"])
        return {
            "Row Number": idx + 1,
            "Restaurant Name": input_data["restaurant"],
            "Review Text": input_data["review"],
            "Status": "Success",
            "Extracted JSON": json.dumps(fb, ensure_ascii=False, indent=2),
            "Error Message": "fallback: empty or invalid primary output",
            "Extraction Tier": tier,
        }
    res = {
        "Row Number": idx + 1,
        "Restaurant Name": input_data["restaurant"],
        "Review Text": input_data["review"],
        "Status": "Success",
        "Extracted JSON": json.dumps(results, ensure_ascii=False, indent=2),
        "Error Message": "",
        "Extraction Tier": tier,
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
    # Removed duplicate hybrid pipeline block (now unified above)




def process_rows(df: pd.DataFrame, cfg: Config, db: DB, logger):
    processed_indices = set()
    results: List[dict] = []
    buffer: List[dict] = []
    error_log: List[dict] = []
    # Use generic cache (previously ollama_*); provide safe defaults if attributes absent
    cache_max = getattr(cfg, 'cache_max', 2000)
    cache_ttl = getattr(cfg, 'cache_ttl_sec', 3600)
    cache = TTLCache(max_size=cache_max, ttl_sec=cache_ttl)

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

        # Add cooldown between batches unless OpenAI calls are disabled
        eff_cooldown = 0
        try:
            if os.getenv("OPENAI_DISABLED", "").strip().lower() not in ("1", "true", "yes"):
                eff_cooldown = max(0, int(cfg.cooldown_sec))
        except Exception:
            eff_cooldown = max(0, int(cfg.cooldown_sec))
        if eff_cooldown > 0:
            time.sleep(eff_cooldown)
            # Ensure cooldown is applied after each batch
            logger.info("Cooldown applied for %d seconds", eff_cooldown)

        start_idx += len(batch)

    overall_elapsed = time.time() - overall_start
    avg_per_row = overall_elapsed / total_rows if total_rows else 0
    projected_100k = avg_per_row * 100000 if avg_per_row else 0
    logger.info("=== Timing summary ===")
    logger.info("Total time: %.2fs for %d rows", overall_elapsed, total_rows)
    logger.info("Average per row: %.3fs", avg_per_row)
    logger.info("Projected for 100,000 rows: %.1f hours (%.1f minutes)", projected_100k/3600, projected_100k/60)

    # Summarize LLM metrics for reconciliation with dashboard
    try:
        from .llm import get_llm_metrics
        metrics = get_llm_metrics(reset=False)
        logger.info(
            "LLM metrics: attempts=%s successes=%s rate_limits=%s other_errors=%s",
            metrics.get("attempts"), metrics.get("successes"), metrics.get("rate_limits"), metrics.get("other_errors"),
        )
    except Exception as e:
        logger.debug("LLM metrics unavailable: %s", e)

    # --- Acceptance summary (no DB needed) ---
    def _parse_json_list(s: str):
        try:
            arr = json.loads(s) if isinstance(s, str) else []
            return arr if isinstance(arr, list) else []
        except Exception:
            return []

    accepted = 0
    rejected = 0
    tier_counts = {}
    tier_accepts = {}
    for r in results:
        tier = r.get("Extraction Tier") or r.get("ExtractionTier") or "unknown"
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        arr = _parse_json_list(r.get("Extracted JSON", ""))
        # A row is accepted if there's at least one object with a valid dish name
        has_valid = False
        for it in arr:
            if isinstance(it, dict):
                d = str(it.get("dish", "")).strip()
                if is_valid_dish_name(d):
                    has_valid = True
                    break
        if has_valid:
            accepted += 1
            tier_accepts[tier] = tier_accepts.get(tier, 0) + 1
        else:
            rejected += 1

    acc_rate = (accepted / total_rows) * 100 if total_rows else 0.0
    logger.info("=== Acceptance summary ===")
    logger.info("Accepted: %d | Rejected: %d | Rate: %.1f%%", accepted, rejected, acc_rate)
    # Per-tier quick view (top 5 tiers by volume)
    top_tiers = sorted(tier_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for t, c in top_tiers:
        ta = tier_accepts.get(t, 0)
        tr = c - ta
        pct = (ta / c * 100) if c else 0.0
        logger.info("Tier %-22s count=%4d accepted=%4d rejected=%4d rate=%.1f%%", t, c, ta, tr, pct)

    # Persist summary next to outputs
    try:
        summary = {
            "total_rows": total_rows,
            "accepted": accepted,
            "rejected": rejected,
            "acceptance_rate_pct": round(acc_rate, 2),
            "by_tier": {
                t: {
                    "count": tier_counts.get(t, 0),
                    "accepted": tier_accepts.get(t, 0),
                    "rejected": tier_counts.get(t, 0) - tier_accepts.get(t, 0),
                    "rate_pct": round((tier_accepts.get(t, 0) / tier_counts.get(t, 1)) * 100, 2) if tier_counts.get(t, 0) else 0.0,
                }
                for t in tier_counts
            },
        }
        with open(os.path.join(cfg.output_dir, "acceptance_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Failed to write acceptance_summary.json: %s", e)

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
