import os
import pandas as pd
from .config import Config
from .logging_setup import setup_logging
from .db import DB
from .processor import process_rows


def run():
    cfg = Config()
    logger = setup_logging(cfg)
    openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    logger.info(
        "Config loaded; input_csv=%s | output_dir=%s | output_csv=%s | rows=[%s,%s) | pg_write_disabled=%s | model=%s",
        cfg.input_csv,
        cfg.output_dir,
        cfg.output_csv or "(default in output_dir)",
        cfg.row_start,
        cfg.row_end,
        cfg.pg_write_disabled,
        openai_model,
    )

    # DB init
    db = DB(cfg, logger)
    db.ensure_table()

    # LLM: no chain needed for OpenAI pipeline

    # Input CSV
    try:
        df_full = pd.read_csv(cfg.input_csv)
    except Exception as e:
        logger.error("Failed to read input CSV %s: %s", cfg.input_csv, e)
        return

    # Validate required columns
    required_cols = {"restaurant_name", "review_text"}
    missing = required_cols - set(df_full.columns)
    if missing:
        logger.error("Input CSV missing required columns: %s | found=%s", sorted(missing), list(df_full.columns))
        return

    # Slice rows
    df = df_full[["restaurant_name", "review_text"]].iloc[cfg.row_start:cfg.row_end].reset_index(drop=True)
    process_rows(df, cfg, db, logger)
