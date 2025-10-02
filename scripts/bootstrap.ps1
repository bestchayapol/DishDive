# Bootstrap the DishDive Python environment on Windows (PowerShell)
# - Creates .venv if missing (using py launcher if available)
# - Upgrades pip/setuptools/wheel
# - Installs pinned requirements
# - Verifies core imports

param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Resolve-Path "$PSScriptRoot\.."
Write-Host "Repo root: $repoRoot" -ForegroundColor Cyan

$venvPy = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPy) -or $Force) {
    if (Test-Path $venvPy) {
        Write-Host "Removing existing .venv (Force)" -ForegroundColor Yellow
        Remove-Item -Recurse -Force (Join-Path $repoRoot '.venv')
    }
    Write-Host "Creating virtual environment (.venv)" -ForegroundColor Cyan
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -m venv (Join-Path $repoRoot '.venv')
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv (Join-Path $repoRoot '.venv')
    } else {
        throw 'No Python interpreter found. Install Python 3.9+ and re-run.'
    }
}

Write-Host "Using venv: $venvPy" -ForegroundColor Green

# Upgrade packaging tools
& $venvPy -m pip install --upgrade pip setuptools wheel

# Install pinned requirements
$req = Join-Path $repoRoot 'requirements.txt'
if (-not (Test-Path $req)) {
    throw "requirements.txt not found at $req"
}
& $venvPy -m pip install -r $req

# Verify core imports
& $venvPy - <<'PY'
import sys
print('Python exec:', sys.executable)
print('Python version:', sys.version)
import numpy, pandas, psycopg2, pydantic
print('numpy:', numpy.__version__, 'pandas:', pandas.__version__)
print('psycopg2 OK, pydantic:', pydantic.__version__)
PY

Write-Host 'Environment bootstrap complete.' -ForegroundColor Green
