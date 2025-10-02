# Run the Go server ensuring the project .venv is preferred and useful env vars are set

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Resolve-Path "$PSScriptRoot\.."
$serverDir = Join-Path $repoRoot 'server'
$venvPy = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $venvPy)) {
    Write-Host 'No .venv found. Run scripts/bootstrap.ps1 first.' -ForegroundColor Yellow
    exit 1
}

# Prefer project venv and add repo root to PYTHONPATH
$env:PYTHON_EXEC = $venvPy
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$($env:PYTHONPATH);$repoRoot" } else { "$repoRoot" }
$env:PYTHONUNBUFFERED = '1'

# Optional safety switches while testing locally
if (-not $env:OPENAI_DISABLED) { $env:OPENAI_DISABLED = '1' }
if (-not $env:WRITE_CHECKPOINT) { $env:WRITE_CHECKPOINT = '0' }
if (-not $env:WRITE_DATA_EXTRACT) { $env:WRITE_DATA_EXTRACT = '0' }

# DB env fallbacks (override with your own local settings if needed)
if (-not $env:PG_HOST) { $env:PG_HOST = 'localhost' }
if (-not $env:PG_PORT) { $env:PG_PORT = '5432' }
if (-not $env:PG_USER) { $env:PG_USER = 'postgres' }
if (-not $env:PG_PASSWORD) { $env:PG_PASSWORD = 'postgres' }
if (-not $env:PG_DATABASE) { $env:PG_DATABASE = 'dishdive' }

Push-Location $serverDir
try {
    go run main.go
} finally {
    Pop-Location
}
