# Go - Python integration (DishDive)

This guide explains how the Go backend (`server/`) connects with the Python LLM pipeline (`llm_processing/`), for both real-time user reviews and batch web reviews.

## Integration modes

- Real-time (user reviews)
  - Trigger: `POST /SubmitReview` from the app.
  - Flow: Go persists the user review -> spawns a Python subprocess to run a single-review extractor -> Python writes JSON extracts to Postgres -> later normalization maps to domain tables.
- Batch (web reviews)
  - Run: Python standalone (from repo root) on a CSV of reviews.
  - Flow: Python processes all rows, writes to Postgres (and CSV reports), then normalization maps to domain tables.

## Shared data contract (Postgres)

- `review_extracts` (written by Python)
  - `rev_ext_id BIGINT PRIMARY KEY`
  - `source_id BIGINT` (row number for web batches, or `UserReview` ID for user submissions)
  - `source_type VARCHAR(64)` (e.g., `web`, `user`)
  - `data_extract TEXT` (JSON array of dish objects)
- Normalized domain tables (queried by Go)
  - `dishes`, `keywords`, `dish_keywords`, `review_dishes`, `review_dish_keywords`, plus restaurant/menu entities.

## Real-time path (SubmitReview)

1. App -> Go: `POST /SubmitReview`
2. Go saves the raw review (gets `reviewID`) and spawns Python:
   - Executable resolution (Windows first):
     - Uses `PYTHON_EXEC` env if set, else prefers `./.venv/Scripts/python.exe`, else `python` on PATH.
   - Working directory and module:
     - Sets subprocess CWD to repo root and runs `-m llm_processing.single_review`.
   - Arguments:
     - `--restaurant "<name>" --review "<text>" --source-type user --source-id <reviewID>`
   - Environment passed:
     - DB: `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`, `PG_SSLMODE`
     - OpenAI: `OPENAI_API_KEY` (and optional `OPENAI_MODEL`, rate-limit knobs)
     - Control: `PG_WRITE_DISABLED=0`, `WRITE_CHECKPOINT=0`, `WRITE_DATA_EXTRACT=0`, `SOURCE_TYPE=user`
     - Hints: `HINT_DISH_ID`, `HINT_RES_ID`, `HINT_DISH_NAME`, `HINT_RES_NAME` (improve extraction)
     - `PYTHONPATH` includes project root
   - Logging: stdout/stderr piped to `server/logs/llm_job_user_<reviewID>.log`.
3. Python extracts dish objects via OpenAI + fallback heuristics and upserts into `review_extracts`.
4. A normalization script (see below) maps those extracts into domain tables used by Go APIs.

Key Go code: `server/internal/service/recommend_service.go` (SubmitReview orchestration).

## Batch path (web reviews)

- Input: CSV with columns `restaurant_name`, `review_text` (from `scripts/final_review_cleaner.py`).
- Run (Windows examples):
  - Batch processor:
    - `python -m llm_processing.main` (or `run_llm_processing.py`)
  - Important env:
    - `INPUT_CSV`, `PG_WRITE_DISABLED=0`, `OUTPUT_DIR`, batching controls (`BATCH_SIZE`, `MAX_WORKERS`), OpenAI envs.
- Outputs:
  - `review_extracts` rows in Postgres
  - CSV: `outputs/processed_reviews.csv`
  - JSON: `outputs/acceptance_summary.json`

## Normalization

- Purpose: Convert `review_extracts.data_extract` (JSON per review) to relational domain rows for queries and recommendations.
- Script: `scripts/llm_related/normalize_extracts_to_domain.py`
  - Supports `--source-type`, `--offset`, `--limit` for incremental runs.
  - Enforces idempotency with uniqueness on `(source_type, source_id, dish_id)`.

## Python modules of interest

- `llm_processing/main.py`: batch entry (reads CSV, processes rows)
- `llm_processing/single_review.py`: thin wrapper for single review job
- `llm_processing/processor.py`: per-row pipeline (prefilter -> LLM -> filter/validate -> fallback) and DB buffering
- `llm_processing/llm.py`: OpenAI v1 client, retries/limits, Thai heuristics, rule-based fallback
- `llm_processing/db.py`: psycopg2 pool/conn; `ensure_table()`, `upsert_review_extracts()`
- `llm_processing/config.py`: env-driven config (DB, batching, caching, controls)

## Environment variables (Python)

- DB: `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`, `PG_SSLMODE`
- OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_MAX_CONCURRENT`, `OPENAI_MIN_INTERVAL_SEC`, `OPENAI_REQUEST_CAP`, retry/backoff knobs
- Controls: `PG_WRITE_DISABLED`, `INPUT_CSV`, `OUTPUT_DIR`, `OUTPUT_CSV`, `ROW_START`, `ROW_END`, `BATCH_SIZE`, `MAX_WORKERS`, `WRITE_CHECKPOINT`, `WRITE_DATA_EXTRACT`, `SOURCE_ID_OFFSET`
- Hints (single review): `HINT_DISH_ID`, `HINT_RES_ID`, `HINT_DISH_NAME`, `HINT_RES_NAME`

## Troubleshooting

- Python not found: set `PYTHON_EXEC` to your interpreter or create a venv at `./.venv`.
- ModuleNotFoundError (`llm_processing`): Go sets `PYTHONPATH` to repo root; for manual runs, invoke from repo root or ensure your `PYTHONPATH` includes the root.
- Postgres write blocked: ensure `PG_WRITE_DISABLED=0`.
- PowerShell parsing of `<` in inline SQL: use the stop-parsing operator `--%`.
- Duplicates on normalization: rely on unique indexes and use `--offset/--limit` for incremental runs.

---

For a higher-level system view, see `docs/architecture.md`.
