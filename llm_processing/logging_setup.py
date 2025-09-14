import logging
from .config import Config

LOGGER_NAME = "dishdive.scraper"

def setup_logging(cfg: Config) -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, cfg.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger(LOGGER_NAME)
    return logger
