# MinIO via Docker for DishDive

This sets up a local MinIO with strong credentials and a pre-created bucket for development.

## Quick start (Windows PowerShell)

1. Generate secrets into `.env` and start MinIO:

```powershell
# From repo root
./scripts/minio/New-MinioSecrets.ps1
./scripts/minio/Start-Minio.ps1
```

2. Generate `config.minio.yaml` with matching credentials (copy the `minio:` block into your existing `config.yaml`):

```powershell
./scripts/minio/Write-BackendConfig.ps1
```

3. Open MinIO Console at http://localhost:9001 and sign in using the credentials written to `.env`.

- S3 endpoint: http://localhost:9000
- Bucket: dishdive (created automatically)

## Environment variables

`.env` contains:

- MINIO_ROOT_USER
- MINIO_ROOT_PASSWORD
- MINIO_BUCKET (default dishdive)

These are consumed by `docker-compose.minio.yml`.

## Stopping MinIO

```powershell
docker compose -f .\docker-compose.minio.yml down
```

Data persists under `./.data/minio/`.
