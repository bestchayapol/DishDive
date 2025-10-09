# Starts MinIO via docker compose with secrets from .env; creates bucket
param(
    [string]$ComposeFile,
    [string]$EnvPath
)

if (-not $ComposeFile -or -not $EnvPath) {
    $repoRoot = (Resolve-Path -Path (Join-Path -Path $PSScriptRoot -ChildPath '..\..')).Path
    if (-not $ComposeFile) { $ComposeFile = Join-Path -Path $repoRoot -ChildPath 'docker-compose.minio.yml' }
    if (-not $EnvPath) { $EnvPath = Join-Path -Path $repoRoot -ChildPath '.env' }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker CLI not found. Install Docker Desktop and retry."
    exit 1
}

if (-not (Test-Path -Path $EnvPath)) {
    Write-Host ".env not found. Generating..." -ForegroundColor Yellow
    & (Join-Path -Path $PSScriptRoot -ChildPath 'New-MinioSecrets.ps1') -EnvPath $EnvPath
}

Write-Host "Starting MinIO using $ComposeFile" -ForegroundColor Cyan
$composeCmd = @(
    'docker','compose','--env-file',"$EnvPath",'-f',"$ComposeFile",'up','-d'
) -join ' '
cmd /c "$composeCmd"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "MinIO is starting. Console: http://localhost:9001  API: http://localhost:9000" -ForegroundColor Green
