# DishDive Go Backend

A Go Fiber backend for DishDive.

## Prerequisites
- Go 1.24+
- MySQL 8+
- MinIO (or S3-compatible) for file uploads

## Configure
Copy the example config and adjust values:

```powershell
Copy-Item -Path .\config.example.yaml -Destination .\config.yaml -Force
```

Edit `config.yaml` as needed.

## Run
From the project root:

```powershell
# Install deps
go mod tidy

# Run
go run .
```

The API will start on `http://localhost:<app.port>` from config.

Health check:
```
GET /health -> ok
```

## Frontend integration
- Base URL: `http://localhost:<app.port>`
- Auth endpoints:
  - POST `/Register` (multipart/form-data with `file` for image)
  - POST `/Login` -> returns `token`
- Auth header for protected routes:
  - `Authorization: Bearer <token>`
- Common routes:
  - GET `/GetCurrentUser`
  - GET `/GetMarketPlace`
  - POST `/PostAddItem` (multipart/form-data with `file`)

CORS is enabled for development (`*`). Consider restricting `AllowOrigins` in production.

## MinIO
- Ensure a bucket exists (currently hardcoded as `needful`).
- Update upload service and URLs if you change bucket or domain.
