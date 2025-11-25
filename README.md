# DishDive

CSC498-499 Capstone Project I-II

DishDive is a cross‑platform Flutter application backed by a Go (Fiber + GORM) API and an auxiliary Python LLM processing pipeline used for ingesting / enriching restaurant reviews. This README covers installation and local development for each component.

## Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Prerequisites Summary](#prerequisites-summary)
3. [Flutter App Setup](#flutter-app-setup)
4. [Go Backend Setup](#go-backend-setup)
5. [Running App Against Local vs Deployed Backend](#running-app-against-local-vs-deployed-backend)
6. [Python LLM Processing Pipeline](#python-llm-processing-pipeline)
7. [Environment Variables Reference](#environment-variables-reference)
8. [Troubleshooting & Tips](#troubleshooting--tips)
9. [Documentation Links](#documentation-links)
10. [Submission Keystore & APK Signing](#submission-keystore--apk-signing)

---

## High-Level Architecture

| Layer               | Tech                                    | Purpose                                                                   |
| ------------------- | --------------------------------------- | ------------------------------------------------------------------------- |
| Mobile / Web Client | Flutter (Dart)                          | User interface, dish browsing, favorites, reviews                         |
| Backend API         | Go (Fiber, GORM, MinIO client, Viper)   | Authentication, restaurant & dish data, favorites, reviews, media storage |
| Review Processing   | Python (pandas, OpenAI API, PostgreSQL) | Batch enrichment & keyword extraction for reviews                         |
| Object Storage      | MinIO                                   | Dish & cuisine images                                                     |
| Database            | PostgreSQL                              | Relational persistence for users, dishes, reviews, keywords               |

---

## Prerequisites Summary

Install the following before starting:

| Component                   | Required Versions / Notes                                               |
| --------------------------- | ----------------------------------------------------------------------- |
| Flutter SDK                 | Stable channel (3.x recommended). Run `flutter doctor`.                 |
| Dart                        | Bundled with Flutter.                                                   |
| Android Studio OR Xcode     | For building Android / iOS respectively.                                |
| Go                          | Go **1.24.x** (per `server/go.mod`).                                    |
| Python                      | Python **3.11+** (3.12 recommended) for LLM pipeline.                   |
| PostgreSQL (optional local) | Needed only if running a local DB instead of remote.                    |
| MinIO (optional local)      | Only if you want local object storage; otherwise use deployed instance. |
| OpenAI API Key              | Required to run Python LLM enrichment (`OPENAI_API_KEY`).               |

---

## Flutter App Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/bestchayapol/DishDive.git
   cd DishDive/dishdive
   ```
2. **Fetch dependencies**
   ```bash
   flutter pub get
   ```
3. **Run analyzer (optional)**
   ```bash
   flutter analyze
   ```
4. **Run on emulator (using local backend)**
   If your Go server runs on `localhost:8080`, Android emulator reaches it via `10.0.2.2`:
   ```bash
   flutter run --dart-define=BACKEND_BASE=http://10.0.2.2:8080
   ```
5. **Run on physical Android device (using local backend)**
   Forward/reverse traffic if needed:
   ```powershell
   adb reverse tcp:8080 tcp:8080
   flutter run --dart-define=BACKEND_BASE=http://localhost:8080
   ```
6. **Run against deployed backend (default in release)**
   Release builds default to the deployed host baked into `ApiConfig`. To override:
   ```bash
   flutter run --dart-define=BACKEND_BASE=http://dishdive.sit.kmutt.ac.th:3000
   ```
7. **Build release APK**
   ```bash
   flutter build apk --release
   adb install -r build/app/outputs/flutter-apk/app-release.apk
   ```
8. **Override backend for release APK (if desired)**
   ```bash
   flutter build apk --release --dart-define=BACKEND_BASE=http://10.0.2.2:8080
   ```

> iOS: supply the same `--dart-define` values when running via Xcode or `flutter build ios`. Ensure appropriate provisioning profiles.

---

## Go Backend Setup

From repository root:

```bash
cd server
go mod download
go build ./...   # optional preflight build
```

### Configuration

`server/config.yaml` contains defaults (port, DB, MinIO, JWT secret). **Do NOT rely on committed secrets in production—rotate and override using environment variables or a local `.env`.**

Order of config resolution:

1. `.env` (loaded by `loadDotEnv` if present)
2. Environment variables (with `.` replaced by `_`, e.g. `db.host` -> `DB_HOST`)
3. `config.yaml` values

### Run

```bash
go run main.go
```

Server listens on `:8080` (configurable via `app.port`).

### Common Endpoints (selected)

| Method | Path                       | Notes                      |
| ------ | -------------------------- | -------------------------- |
| POST   | /Login                     | Auth (returns token)       |
| GET    | /GetRestaurantMenu/:resID  | Requires `?userID=`        |
| GET    | /GetDishDetail/:dishID     | Requires `?userID=`        |
| GET    | /GetFavoriteDishes/:userID | Favorites list             |
| POST   | /AddFavorite               | Body: `{user_id, dish_id}` |
| DELETE | /RemoveFavorite            | Body: `{user_id, dish_id}` |
| GET    | /GetDishReviewPage/:dishID | Review metadata            |
| POST   | /SubmitReview              | Submit a review            |

---

## Running App Against Local vs Deployed Backend

The Flutter app computes its base URL dynamically. Summary:

| Scenario               | Default Base URL                        | Override                                           |
| ---------------------- | --------------------------------------- | -------------------------------------------------- |
| Android emulator (dev) | `http://10.0.2.2:8080` (if you specify) | `--dart-define=BACKEND_BASE=...`                   |
| Physical device (dev)  | (Use LAN IP or reverse)                 | `--dart-define=BACKEND_BASE=http://<your_ip>:8080` |
| Release build          | Deployed host baked in                  | Provide `--dart-define` at build time              |

If a dish page was opened via Favorites and lacked `res_id`, the client now auto‑fetches review metadata to restore it (see `DishPage` fallback logic).

---

## Python LLM Processing Pipeline

Located under `llm_processing/` with a thin runner `run_llm_processing.py` at repo root.

### Purpose

Reads a CSV of raw user / web reviews, processes them (LLM enrichment, keyword extraction, sentiment summary), and (optionally) writes structured rows back to PostgreSQL.

### Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Required Environment

Set only:

```
OPENAI_API_KEY=sk-...
```

**That's it!** The script includes sensible defaults for testing (processes 10 rows, connects to deployed database, enables DB writes, outputs to `outputs/processed_reviews.csv`).

### Run

```bash
python run_llm_processing.py
```

Outputs:

- Processed CSV under `outputs/` (default filename if `OUTPUT_CSV` not supplied)
- Logs to stdout with timing + progress

### Notes

- The script now defaults to processing only 10 rows and enables database writes for easy testing.
- To process more data, set `ROW_END` to a higher value (e.g., `ROW_END=1000`).
- To disable database writes during testing, set `PG_WRITE_DISABLED=true`.
- `OPENAI_MODEL` may be set (defaults to `gpt-4o-mini`).

---

## Environment Variables Reference

| Group         | Key                           | Description                     | Default               |
| ------------- | ----------------------------- | ------------------------------- | --------------------- |
| Flutter Build | BACKEND_BASE                  | Override backend base URL       | internal logic        |
| Go Server     | DB\__ / db._                  | Database connection pieces      | see `config.yaml`     |
| Go Server     | MINIO\__ / minio._            | MinIO storage settings          | see `config.yaml`     |
| Go Server     | JWT_JWTSECRET / jwt.jwtSecret | JWT signing secret              | "DishDive" (replace!) |
| Python        | INPUT_CSV                     | Source reviews CSV              | reviews.csv           |
| Python        | OUTPUT_DIR                    | Output folder                   | outputs               |
| Python        | OUTPUT_CSV                    | Explicit output file name       | auto-generated        |
| Python        | OPENAI_API_KEY                | API key for LLM calls           | (required)            |
| Python        | OPENAI_MODEL                  | Model name                      | gpt-4o-mini           |
| Python        | PG\_\*                        | PostgreSQL connectivity         | testing host values   |
| Python        | PG_WRITE_DISABLED             | Block DB writes when true       | true                  |
| Python        | BATCH_SIZE                    | Batch size per processing cycle | 25                    |
| Python        | MAX_WORKERS                   | Concurrency for workers         | 4                     |

---

## Setting Up OpenAI API Key

To use the OpenAI-powered features in this project, you need an OpenAI API key.

1. **Create an OpenAI Account**:

   - Go to [https://platform.openai.com/signup/](https://platform.openai.com/signup/) and sign up for an account.

2. **Generate an API Key**:

   - Log in to the OpenAI dashboard.
   - Navigate to the API Keys section and click "Create new secret key."
   - Copy the generated key.

3. **Add the Key to `.env`**:
   - Open the `.env` file in the `server/` directory.
   - Add the following line:
     ```plaintext
     OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     ```

**Note**: OpenAI API usage incurs costs. Please use your own API key for testing.

---

## Google Maps API Key Setup (Optional)

The Google Maps API key is used for geocoding functionality in some parts of the project:

- `server/internal/handler/food.go`: Contains example code for calling the Google Geocoding API
- `scripts/llm_related/geocode_restaurants.py`: Implements geocoding functionality

**For testing/submission purposes, this is optional since the core app functionality works without it.**

If you want to set it up:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services > Credentials**
4. Click **Create Credentials** and select **API Key**
5. Enable the **Geocoding API** for your project
6. Copy the generated API key

**For simplicity, no restrictions are needed** - the key can be left unrestricted for testing purposes.

---

## Troubleshooting & Tips

| Issue                                 | Hint                                                                                                                      |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Emulator cannot reach local server    | Use `10.0.2.2` or `adb reverse tcp:8080 tcp:8080` for device.                                                             |
| Favorites dish lacks review button    | Fixed via fallback fetch of `GetDishReviewPage`. Update to latest code.                                                   |
| MinIO images not loading              | Verify extension (e.g., `.jpg` vs `.jpeg`) matches DB `image_link`.                                                       |
| OpenAI rate limits                    | Lower `BATCH_SIZE` or raise `TARGET_BATCH_SEC`. Implement cooldown via env knobs.                                         |
| Google Maps functionality not working | Ensure API key is set up and Geocoding API is enabled in Google Cloud Console. SHA‑1 restrictions not needed for testing. |

---

## Documentation Links

- Architecture & Tech Stack: `docs/architecture.md`
- Go–Python Integration: `docs/go-python-integration.md`

---

### ⚠ Security Notice

Credentials and secrets in `config.yaml` are for development convenience. **Always replace them and use environment variables / secret managers in production.** Rotate any exposed keys immediately.

---

## APK Building for Submission

For a consistent release build:

1. **Simple Release Build**:

   ```powershell
   cd dishdive
   flutter build apk --release
   ```

2. **Install on Device/Emulator**:

   ```powershell
   adb install -r build/app/outputs/flutter-apk/app-release.apk
   ```

**Note**: The app will use the default debug keystore, which is sufficient for testing and submission since no API key restrictions are needed.

---

## Troubleshooting & Common Pitfalls

| Issue                                   | Hint                                                                              |
| --------------------------------------- | --------------------------------------------------------------------------------- |
| Emulator cannot reach local server      | Use `10.0.2.2` or `adb reverse tcp:8080 tcp:8080` for device.                     |
| Favorites dish lacks review button      | Fixed via fallback fetch of `GetDishReviewPage`. Update to latest code.           |
| MinIO images not loading                | Verify extension (e.g., `.jpg` vs `.jpeg`) matches DB `image_link`.               |
| OpenAI rate limits                      | Lower `BATCH_SIZE` or raise `TARGET_BATCH_SEC`. Implement cooldown via env knobs. |
| Google Maps functionality not working   | Ensure API key is set up and Geocoding API is enabled in Google Cloud Console.    |
| Python script writes to DB unexpectedly | Ensure `PG_WRITE_DISABLED=true` while testing.                                    |
| MinIO image 404                         | Confirm filename & extension match DB `image_link`.                               |
| R8 missing classes error                | Shrinking disabled; if re‑enabled add Play Core keep rules.                       |

---
