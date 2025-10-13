# DishDive Architecture & Tech Stack

This document explains the end-to-end architecture of DishDive, the main technologies in each layer, and how the pieces connect in runtime data flows. It’s meant for new contributors and for quick orientation when debugging.

## High-level overview

- Client app: Flutter/Dart (Android/iOS/Web)
  - State management: Provider
  - Networking: Dio
  - Persistence: SharedPreferences
  - Maps & Location: google_maps_flutter, geolocator
  - Media: image_picker, cached_network_image
- API server: Go
  - Web framework: Fiber v2
  - ORM: GORM with Postgres driver
  - Config: Viper (+ simple .env loader)
  - Auth: JWT (v4)
  - Object storage: MinIO client (S3-compatible)
- Data/AI pipeline: Python
  - Libraries: pandas, psycopg2-binary, openai>=1,<2, pydantic, beautifulsoup4, rapidfuzz, pythainlp
  - Purpose: extract dish-level data from reviews (LLM + rule-based) and write to Postgres for normalization
- Storage/infra
  - Database: Postgres (hosted on university VM)
  - Object storage: MinIO (local Docker Compose; S3-compatible)

```
Flutter (Dio + Provider) ──HTTP──▶ Go API (Fiber + GORM) ──SQL──▶ Postgres
                │                            │
                │                            └──S3──▶ MinIO (images)
                │
                └──(User submits review)──▶ Go spawns Python (LLM) ──SQL──▶ Postgres (review_extracts)
```

## Repositories & layout

- Flutter app: `dishdive/`
- Go backend: `server/`
- Python LLM/ETL: `llm_processing/`
- Data cleaning scripts: `scripts/` (e.g., `scripts/final_review_cleaner.py`)
- Outputs: `outputs/` (batch CSV results/diagnostics)

## Frontend (Flutter)

- Declared in `dishdive/pubspec.yaml`:
  - `provider`, `dio`, `shared_preferences`, `google_maps_flutter`, `geolocator`, `image_picker`, `cached_network_image`, `web_socket_channel` (present, not core to main flows)
- Base URL and endpoints: `dishdive/lib/Utils/api_config.dart`
  - Example endpoints used by the app:
    - Auth: `POST /Register`, `POST /Login`
    - User: `GET /GetCurrentUser`, `GET /GetUserByToken`, `GET /GetUserByUserId/:UserID`
    - Food: `POST /SearchRestaurantsByDish`, `GET /GetRestaurantList`, `GET /GetRestaurantMenu/:resID`, `GET /GetRestaurantLocations/:resID`, `GET /GetDishDetail/:dishID`
    - Favorites: `GET /GetFavoriteDishes/:userID`, `POST /AddFavorite`, `DELETE /RemoveFavorite`
    - Recommendations/Reviews: `GET /GetUserSettings/:userID`, `POST /UpdateUserSettings/:userID`, `GET /GetDishReviewPage/:dishID`, `POST /SubmitReview`, `GET /GetRecommendedDishes/:userID`
    - Storage: `POST /upload`
- Auth & state
  - `TokenProvider` stores JWT and `userId`, persisted via `SharedPreferences` (`lib/provider/token_provider.dart`).
  - Requests include `Authorization: Bearer <token>` when available.
- Services call the API with Dio (e.g., `lib/services/restaurant_service.dart`, `lib/services/auth_service.dart`).
- Maps & location
  - `google_maps_flutter` + `geolocator`; map-related widgets/pages reference `LocationProvider`.

## Backend (Go)

- Entry: `server/main.go`
  - Web: Fiber v2
  - ORM: GORM with Postgres driver
  - Config: Viper (`config.yaml` + environment overrides) and a small `.env` reader
  - Timezone: `Asia/Bangkok`
  - MinIO: `github.com/minio/minio-go/v7`
- Auto-migrations (subset, see `main.go`):
  - `User`, `Restaurant`, `RestaurantLocation`, `Dish`, `DishAlias`, `Keyword`, `KeywordAlias`, `Favorite`, `DishKeyword`, `PreferenceBlacklist`, `UserReview`, `ReviewDish`, `ReviewDishKeyword`, `WebReview`, `ReviewExtract`, `CuisineImage`
- Handlers/services/repositories under `server/internal/...` implement:
  - Users: register/login/profile; JWT handling in services (middleware scaffold exists but is commented)
  - Food: list/search/menu/locations/favorites
  - Recommendations: user settings (unified), dish review page, recommending dishes
  - Storage: image upload endpoint writes to MinIO and returns a URL
- MinIO runtime
  - `server/docker-compose.minio.yml` boots MinIO and an `mc` sidecar to create a bucket and set anonymous download (for dev).

### Python orchestration on review submit

When the app calls `POST /SubmitReview`:

1. Server persists the review and gets a `reviewID`.
2. Server spawns a Python process: `python -m llm_processing.single_review --restaurant <name> --review <text> --source-id <reviewID> --source-type user`.
   - Passes DB env (PG_HOST/PORT/USER/PASSWORD/DATABASE/SSL), OpenAI envs, and control flags: `PG_WRITE_DISABLED=0`, `WRITE_CHECKPOINT=0`, `WRITE_DATA_EXTRACT=0`.
   - Injects hints: `HINT_DISH_ID`, `HINT_RES_ID`, `HINT_DISH_NAME`, `HINT_RES_NAME` to improve extraction.
   - Sets `PYTHONPATH` and working directory to the repo root; prefers local venv if present (`./.venv`).
3. Python extracts dish-level JSON and upserts to Postgres table `review_extracts`.
4. A separate normalization step (scripted) converts `review_extracts.data_extract` into domain tables (dish/keyword links, counts, sentiment), enabling recommendations.

## Data/AI pipeline (Python `llm_processing/`)

- Entrypoints
  - Batch: `python -m llm_processing.main` (or `run_llm_processing.py` wrapper)
  - Single review: `python -m llm_processing.single_review` (used by Go server)
- Key modules
  - `config.py`: env-driven configuration (CSV paths, batching, DB, caching)
  - `db.py`: psycopg2 connections/pool; creates `review_extracts` if absent; `upsert_review_extracts()`
  - `llm.py`: OpenAI Chat Completions client (v1), retries/limits, Thai-specific heuristics, rule-based fallback
  - `processor.py`: per-row extraction pipeline (prefilter → LLM → validate/filter → fallback) and batch buffering
  - `utils.py`: Thai NLP helpers (keywords, dish validation, TTL cache, sentiment inference)
- Table shape used by Python (created if missing):
  - `review_extracts(rev_ext_id BIGINT PK, source_id BIGINT, source_type VARCHAR(64), data_extract TEXT)`
- Batch ingestion flow
  - Input CSV must contain: `restaurant_name`, `review_text`.
  - Writes accepted rows to `review_extracts` (JSON list of dish objects), and writes a CSV report in `outputs/`.
  - Acceptance summary written to `outputs/acceptance_summary.json`.
  - Normalization scripts (in `scripts/llm_related/`) should then map extracts into domain tables.

## Configuration

- Go server
  - `server/config.yaml` (or `server/config/config.yaml`) via Viper; environment variables override (periods replaced by underscores)
  - Simple `.env` loader reads `.env` or `../.env`
  - Note: `server/README.md` mentions MySQL, but the code uses Postgres drivers; treat the MySQL note as outdated.
- Python
  - Environment variables configure DB and OpenAI:
    - Postgres: `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`, `PG_SSLMODE`
    - LLM: `OPENAI_API_KEY`, `OPENAI_MODEL`, plus optional `OPENAI_DISABLED`, retry/backoff and budget caps
    - Control: `INPUT_CSV`, `OUTPUT_DIR`, `OUTPUT_CSV`, `ROW_START`, `ROW_END`, `BATCH_SIZE`, `MAX_WORKERS`, `PG_WRITE_DISABLED`, `WRITE_CHECKPOINT`, `WRITE_DATA_EXTRACT`, `SOURCE_ID_OFFSET`
- Flutter
  - API base URL set in `dishdive/lib/Utils/api_config.dart` (`10.0.2.2:8080` for Android emulator). Adjust per environment or device.
- MinIO
  - `server/docker-compose.minio.yml` provides local S3-compatible object storage. Bucket is created by the `mc` sidecar.

## Typical data flows

1. Login & user data

   - App → `POST /Login` → receives JWT → stored in `TokenProvider` → subsequent requests include `Authorization` header → `GET /GetCurrentUser`.

2. Browse restaurants & favorites

   - App → `GET /GetRestaurantList` / `GET /GetRestaurantMenu/:resID`.
   - App → `POST /AddFavorite` or `DELETE /RemoveFavorite`.

3. Submit review with AI extraction

   - App → `POST /SubmitReview`.
   - Go saves review, spawns Python job → Python writes to `review_extracts`.
   - Normalization job maps extracts to domain tables → recommendations use updated signals.

4. Batch ingestion (web reviews)
   - Clean/prepare CSV (e.g., `scripts/final_review_cleaner.py` output with `restaurant_name`, `review_text`).
   - Run `llm_processing.main` with `PG_WRITE_DISABLED=0` to write.
   - Normalize into domain tables.

## Where to look in code

- Flutter
  - Endpoints & headers: `dishdive/lib/Utils/api_config.dart`
  - Auth state: `dishdive/lib/provider/token_provider.dart`
  - Service calls: `dishdive/lib/services/*.dart`
- Go
  - Server wiring & routes: `server/main.go`
  - Handlers/services/repos: `server/internal/**`
  - MinIO compose: `server/docker-compose.minio.yml`
- Python
  - Entrypoints: `llm_processing/main.py`, `llm_processing/single_review.py`
  - Core: `llm_processing/processor.py`, `llm_processing/llm.py`, `llm_processing/db.py`, `llm_processing/utils.py`

---

If you want a diagram image instead of the ASCII sketch, open an issue and we can add a generated diagram to this page.
