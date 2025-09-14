import os
import pandas as pd
from .config import Config
from .logging_setup import setup_logging
from .db import DB
from .llm import build_chain
from .processor import process_rows


def run():
    cfg = Config()
    logger = setup_logging(cfg)
    logger.info("Config loaded; output_dir=%s", cfg.output_dir)

    # DB init
    db = DB(cfg, logger)
    db.ensure_table()

    # LLM
    llm, chain = build_chain(cfg)

    # Input CSV
    try:
        df_full = pd.read_csv(cfg.input_csv)
    except Exception as e:
        logger.error("Failed to read input CSV %s: %s", cfg.input_csv, e)
        return

    # Slice rows
    df = df_full[["restaurant_name", "review_text"]].iloc[cfg.row_start:cfg.row_end].reset_index(drop=True)

    process_rows(df, cfg, chain, db, logger)
