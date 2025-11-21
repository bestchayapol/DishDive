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
10. [Fresh Machine Setup (Full Environment)](#fresh-machine-setup-full-environment)

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

### Maps / External Keys

Add any required keys (e.g., Google Maps) to your platform-specific manifests. Restrict them by SHA‑1 of your signing certificate for production.

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

### Example `.env`

```
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_DATABASE=dishdive
MINIO_HOST=localhost
MINIO_PORT=9000
MINIO_ACCESSKEY=admin
MINIO_SECRETKEY=supersecret
JWT_JWTSECRET=replace_this_in_prod
OPENAI_API_KEY=sk-xxx (only if server later validates something against OpenAI)
```

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

Set at minimum:

```
OPENAI_API_KEY=sk-...
INPUT_CSV=restaurant_reviews.csv          # or your file
PG_WRITE_DISABLED=true                    # keep true while experimenting
```

Optional performance/env tweaks (defaults shown):

```
BATCH_SIZE=25
MAX_WORKERS=4
ROW_START=0
ROW_END=1000
TARGET_BATCH_SEC=10.0
PREFILTER_ENABLED=false
LOG_LEVEL=INFO
PG_HOST=dishdive.sit.kmutt.ac.th
PG_PORT=5432
PG_USER=root
PG_PASSWORD=***
PG_DATABASE=testing
PG_SSLMODE=disable
```

### Run

```bash
python run_llm_processing.py
```

Outputs:

- Processed CSV under `outputs/` (default filename if `OUTPUT_CSV` not supplied)
- Logs to stdout with timing + progress

### Notes

- Set `PG_WRITE_DISABLED=false` ONLY when you are confident writes should occur.
- For rapid local testing, reduce `ROW_END` and `BATCH_SIZE`.
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

## Troubleshooting & Tips

| Issue                              | Hint                                                                                           |
| ---------------------------------- | ---------------------------------------------------------------------------------------------- |
| Emulator cannot reach local server | Use `10.0.2.2` or `adb reverse tcp:8080 tcp:8080` for device.                                  |
| Favorites dish lacks review button | Fixed via fallback fetch of `GetDishReviewPage`. Update to latest code.                        |
| MinIO images not loading           | Verify extension (e.g., `.jpg` vs `.jpeg`) matches DB `image_link`.                            |
| OpenAI rate limits                 | Lower `BATCH_SIZE` or raise `TARGET_BATCH_SEC`. Implement cooldown via env knobs.              |
| SHA-1 key restriction failing      | Use Gradle `signingReport` for correct SHA‑1 of signing keystore, not pairing RSA fingerprint. |

---

## Documentation Links

- Architecture & Tech Stack: `docs/architecture.md`
- Go–Python Integration: `docs/go-python-integration.md`

---

### ⚠ Security Notice

Credentials and secrets in `config.yaml` are for development convenience. **Always replace them and use environment variables / secret managers in production.** Rotate any exposed keys immediately.

---

## Fresh Machine Setup (Full Environment)

This section assumes a brand‑new Windows machine with no development tooling installed. The installation video you produce should focus ONLY on code dependencies (Flutter, Go modules, Python packages). The README covers both code and non‑code tooling so anyone can reproduce your environment from scratch.

### 0. System Prep

- Recommended OS: Windows 10/11 64‑bit (latest updates applied)
- Ensure you have at least 15 GB free disk space (Flutter SDK + Android SDK + Go + Python env + caches)

### 1. Core Tools (GUI + Editors)

| Tool                      | Purpose                        | Install                              | Verify                               |
| ------------------------- | ------------------------------ | ------------------------------------ | ------------------------------------ |
| Git                       | Version control                | https://git-scm.com/download/win     | `git --version`                      |
| VS Code                   | Primary editor                 | https://code.visualstudio.com/       | Launch `code` (optional add to PATH) |
| GitHub Desktop (optional) | GUI Git client                 | https://desktop.github.com/          | Sign in & clone repo                 |
| Android Studio            | Android SDK / emulators        | https://developer.android.com/studio | Start & run SDK Manager              |
| Anaconda (Python)         | Python distribution / env mgmt | https://www.anaconda.com/download    | `conda --version`                    |
| Go                        | Backend server                 | https://go.dev/dl/                   | `go version`                         |
| OpenJDK (bundled)         | Android build toolchain        | Installed via Android Studio (JBR)   | `java -version`                      |

### 2. Install Flutter SDK

1. Download latest stable from https://flutter.dev/docs/get-started/install/windows
2. Extract to `C:\src\flutter` (recommended path)
3. Add `C:\src\flutter\bin` to PATH (System Environment Variables)
4. In new PowerShell window: `flutter doctor` and install any missing components (Android licenses: `flutter doctor --android-licenses`)

### 3. Android Toolchain

Open Android Studio:

1. SDK Manager: Install latest Android SDK (e.g. API 34) + Android SDK Platform Tools.
2. AVD Manager: Create a Pixel/ARM64 emulator.
3. Accept all licenses: `flutter doctor --android-licenses`.

### 4. Clone Repository

```powershell
git clone https://github.com/bestchayapol/DishDive.git
cd DishDive
```

Recommended layout:

```
DishDive/            # repo root
   dishdive/          # Flutter client
   server/            # Go backend
   llm_processing/    # Python pipeline
```

### 5. Flutter Project Dependencies

```powershell
cd dishdive
flutter pub get
flutter analyze  # optional
```

Run on emulator (local backend later):

```powershell
flutter run --dart-define=BACKEND_BASE=http://10.0.2.2:8080
```

### 6. Go Backend

Install Go (already verified via `go version`). Then:

```powershell
cd ..\server
go mod download
go run main.go
```

Server default port: 8080. Leave running in its own terminal.

#### Optional: Local PostgreSQL & MinIO

If not using remote services:
| Service | Quick Start |
|---------|-------------|
| PostgreSQL | Install via installer or Docker; create database `dishdive`. Update env vars / config.yaml. |
| MinIO | `docker run -p 9000:9000 -p 9001:9001 -e MINIO_ROOT_USER=admin -e MINIO_ROOT_PASSWORD=supersecret quay.io/minio/minio server /data --console-address ":9001"` |

Update `server/config.yaml` or `.env` accordingly.

### 7. Python (Anaconda Environment)

Create environment:

```powershell
conda create -n dishdive-py python=3.12 -y
conda activate dishdive-py
pip install --upgrade pip
pip install -r requirements.txt
```

Run processing (ensure `restaurant_reviews.csv` exists or adjust `INPUT_CSV`):

```powershell
python run_llm_processing.py
```

Set core env vars first (PowerShell example):

```powershell
$env:OPENAI_API_KEY="sk-xxxx"
$env:INPUT_CSV="restaurant_reviews.csv"
$env:PG_WRITE_DISABLED="true"
```

### 8. Backend ↔ Flutter Connectivity

- Emulator uses `10.0.2.2:8080` for host machine’s `localhost:8080`.
- Physical device: `adb reverse tcp:8080 tcp:8080` then backend URL is `http://localhost:8080`.
- Release APK: defaults to deployed host (no `--dart-define` needed unless overriding).

### 9. Signing & Maps API (Submission)

Generate keystore (inside `dishdive/android/app/keystore`):

```powershell
keytool -genkeypair -v -storetype PKCS12 -alias submission -keyalg RSA -keysize 2048 -validity 365 `
   -keystore submission.keystore -storepass submitBuild -keypass submitBuild `
   -dname "CN=Submission, OU=Capstone, O=DishDive, L=Bangkok, S=Bangkok, C=TH"
```

Add to `dishdive/android/gradle.properties`:

```properties
SUBMISSION_STORE_FILE=keystore/submission.keystore
SUBMISSION_STORE_PASSWORD=submitBuild
SUBMISSION_KEY_ALIAS=submission
SUBMISSION_KEY_PASSWORD=submitBuild
```

Build:

```powershell
cd dishdive
flutter build apk --release
```

Get SHA‑1:

```powershell
cd android
./gradlew signingReport
```

Restrict Google Maps API key: Android apps → package `com.example.dishdive` + SHA‑1 from report.

### 10. Path & Verification Checklist

| Command                                | Expectation                            |
| -------------------------------------- | -------------------------------------- |
| `flutter doctor`                       | All checks green / minor warnings only |
| `go version`                           | Shows 1.24.x                           |
| `conda env list`                       | Includes `dishdive-py`                 |
| `python -c "import pandas"`            | No errors                              |
| `curl http://localhost:8080/EnvStatus` | Env status JSON (backend running)      |

### 11. Common Pitfalls

| Pitfall                                 | Fix                                                         |
| --------------------------------------- | ----------------------------------------------------------- |
| Emulator can’t reach backend            | Use `10.0.2.2` or enable reverse for device.                |
| Missing SHA‑1 for Maps key              | Run `./gradlew signingReport` in `android/`.                |
| Python script writes to DB unexpectedly | Ensure `PG_WRITE_DISABLED=true` while testing.              |
| MinIO image 404                         | Confirm filename & extension match DB `image_link`.         |
| R8 missing classes error                | Shrinking disabled; if re‑enabled add Play Core keep rules. |

---
