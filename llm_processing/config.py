import os
from dataclasses import dataclass

def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default

def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except Exception:
        return default

def _bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}

@dataclass(frozen=True)
class Config:
    # IO
    input_csv: str = os.environ.get("INPUT_CSV", "reviews.csv")
    output_dir: str = os.environ.get("OUTPUT_DIR", "outputs")
    # Single-output CSV path (if empty, a default name under output_dir will be used)
    output_csv: str = os.environ.get("OUTPUT_CSV", "")
    # Process all rows by default
    row_start: int = _int("ROW_START", 0)
    row_end: int = _int("ROW_END", 2_147_483_647)

    # Processing
    batch_size: int = _int("BATCH_SIZE", 25)
    max_workers: int = _int("MAX_WORKERS", 4)
    cooldown_sec: int = _int("COOLDOWN_BASE_SEC", 5)
    target_batch_sec: float = _float("TARGET_BATCH_SEC", 10.0)
    prefilter_enabled: bool = _bool("PREFILTER_ENABLED", False)

    # DB
    pg_host: str = os.environ.get("PGHOST", os.environ.get("PG_HOST", "dishdive.sit.kmutt.ac.th"))
    pg_port: int = _int("PGPORT", int(os.environ.get("PG_PORT", 5432)))
    pg_user: str = os.environ.get("PGUSER", os.environ.get("PG_USER", "root"))
    pg_password: str = os.environ.get("PGPASSWORD", os.environ.get("PG_PASSWORD", "tungtungtungtungsahur"))
    pg_database: str = os.environ.get("PGDATABASE", os.environ.get("PG_DATABASE", "testing"))
    pg_sslmode: str = os.environ.get("PG_SSLMODE", "disable")
    # Default to disabling DB writes unless explicitly enabled
    pg_write_disabled: bool = _bool("PG_WRITE_DISABLED", True)
    pg_pool_min: int = _int("PG_POOL_MIN", 1)
    pg_pool_max: int = _int("PG_POOL_MAX", 5)

    # Logging
    log_level: str = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Output gating (single file by default)
    write_checkpoint: bool = _bool("WRITE_CHECKPOINT", False)
    write_data_extract: bool = _bool("WRITE_DATA_EXTRACT", False)

    # Generic in-memory cache (replaces old ollama_* cache knobs)
    cache_max: int = _int("CACHE_MAX", 2000)
    cache_ttl_sec: int = _int("CACHE_TTL_SEC", 3600)

    # Source ID adjustment for review_extracts ingestion
    source_id_offset: int = _int("SOURCE_ID_OFFSET", 0)
