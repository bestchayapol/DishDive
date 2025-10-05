"""Incremental normalization for a single newly inserted review_extract row.

This mirrors the logic in scripts/normalize_extracts_to_domain.py but restricts
processing to one (source_id, source_type) so we can update domain tables soon
after an LLM extract is written. We avoid DDL here – the main application
should manage schema creation.
"""
from __future__ import annotations

import json
from typing import List, Optional
import psycopg2

from .config import Config
from .logging_setup import setup_logging
from .normalize_core import NormalizationContext
from .utils import build_fallback_entries


def needs_fallback(raw: Optional[str]) -> bool:
    return not raw or raw.strip() == "" or raw.strip() in ("[]","null","None")


def normalize_single(source_id: int, source_type: str = "user") -> bool:
    cfg = Config()
    logger = setup_logging(cfg)
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
        with conn.cursor() as cur:
            # Distinguish by source_type if the column exists; otherwise legacy behavior.
            has_source_type = False
            try:
                cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name='review_dishes' AND column_name='source_type'")
                if cur.fetchone():
                    has_source_type = True
            except Exception:
                conn.rollback()
            try:
                if has_source_type:
                    cur.execute("SELECT 1 FROM review_dishes WHERE source_id=%s AND source_type=%s LIMIT 1", (source_id, source_type))
                else:
                    cur.execute("SELECT 1 FROM review_dishes WHERE source_id=%s LIMIT 1", (source_id,))
            except Exception as e:
                # If this failed, rollback and fallback to legacy without stopping the flow.
                conn.rollback()
                if has_source_type:
                    # Retry without source_type
                    with conn.cursor() as cur2:
                        cur2.execute("SELECT 1 FROM review_dishes WHERE source_id=%s LIMIT 1", (source_id,))
                        if cur2.fetchone():
                            logger.info("Normalization skip: source_id=%s (legacy fallback) already normalized", source_id)
                            return True
                else:
                    logger.error("Skip check query failed unexpectedly: %s", e)
            else:
                if has_source_type and cur.fetchone():
                    logger.info("Normalization skip: source_id=%s type=%s already normalized", source_id, source_type)
                    return True
                else:
                    # If legacy schema (no source_type col) we proceed even if a row exists, relying on (source_id,dish_id) dedupe to avoid duplication.
                    pass
            # Fetch the extract row (must include source_type filter if available)
            if has_source_type:
                cur.execute("SELECT rev_ext_id, data_extract FROM review_extracts WHERE source_id=%s AND source_type=%s ORDER BY rev_ext_id DESC LIMIT 1", (source_id, source_type))
            else:
                cur.execute("SELECT rev_ext_id, data_extract FROM review_extracts WHERE source_id=%s ORDER BY rev_ext_id DESC LIMIT 1", (source_id,))
            row = cur.fetchone()
            if not row:
                logger.warning("No review_extract for source_id=%s type=%s", source_id, source_type)
                return False
            rev_ext_id, data_extract = row
        ctx = NormalizationContext(conn, logger)
        ctx.current_source_type = source_type
        # First attempt: let core salvage raw serialization (JSON or python-literal)
        stats = ctx.normalize_extract_row(source_id, data_extract)
        if not stats.get("processed") and needs_fallback(data_extract):
            # Only synthesize fallback if truly empty raw extract
            import os
            hint_res = os.environ.get("HINT_RES_NAME", "").strip()
            hint_dish = os.environ.get("HINT_DISH_NAME", "").strip()
            hint_dish_id = os.environ.get("HINT_DISH_ID", "").strip()
            review_text = os.environ.get("HINT_REVIEW_TEXT", "")
            fb = []
            if hint_dish or hint_dish_id:
                fb = build_fallback_entries(hint_res or "", review_text)
                if fb:
                    fb[0]["dish"] = hint_dish or f"dish_id:{hint_dish_id}"
                    if "_hints" not in fb[0]:
                        fb[0]["_hints"] = {}
                    if hint_dish_id.isdigit():
                        fb[0]["_hints"]["dish_id"] = int(hint_dish_id)
                if not fb and (hint_dish or hint_dish_id):
                    fb = [{
                        "restaurant": hint_res or "",
                        "dish": hint_dish or f"dish_id:{hint_dish_id}",
                        "cuisine": "thai",
                        "restriction": None,
                        "sentiment": {"positive": [], "negative": []},
                        "_hints": {"dish_id": int(hint_dish_id) if hint_dish_id.isdigit() else None}
                    }]
            if fb:
                logger.info("Fallback synthesized for empty extract source_id=%s (restaurant=%r dish=%r)", source_id, fb[0].get("restaurant"), fb[0].get("dish"))
                stats = ctx.normalize_extract_row(source_id, json.dumps(fb, ensure_ascii=False))
        if stats.get("processed"):
            ctx.recompute_scores_and_restaurants()
        logger.info("Incremental normalization complete for source_id=%s stats=%s", source_id, stats)
        return True
    except Exception as e:
        logger.error("Incremental normalization error: %s", e)
        return False
    finally:
        try: conn.close()
        except Exception: pass

if __name__ == "__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-id", type=int, required=True)
    ap.add_argument("--source-type", default="user")
    a=ap.parse_args()
    ok=normalize_single(a.source_id, a.source_type)
    raise SystemExit(0 if ok else 1)
