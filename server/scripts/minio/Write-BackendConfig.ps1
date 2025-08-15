# Writes a standalone config.minio.yaml with minio.* values based on .env (non-destructive)
param(
    [string]$EnvPath,
    [string]$ConfigPath
)

# Resolve repo root and defaults
$repoRoot = (Resolve-Path -Path (Join-Path -Path $PSScriptRoot -ChildPath '..\..')).Path
if (-not $EnvPath)     { $EnvPath     = Join-Path -Path $repoRoot -ChildPath '.env' }
if (-not $ConfigPath)  { $ConfigPath  = Join-Path -Path $repoRoot -ChildPath 'config.minio.yaml' }

if (-not (Test-Path -Path $EnvPath)) { throw ".env not found at $EnvPath" }

# Load .env into a dictionary
$envData = @{}
Get-Content $EnvPath | ForEach-Object {
    if ($_ -match '^\s*#') { return }
    if ($_ -match '^\s*$') { return }
    $k, $v = $_ -split '=', 2
    if ($k) { $envData[$k.Trim()] = ($v.Trim()) }
}

function Get-EnvVar([string]$name, [string]$default = $null) {
    if ($envData.ContainsKey($name)) {
        $val = $envData[$name]
        if (-not [string]::IsNullOrWhiteSpace($val)) { return $val }
    }
    return $default
}

function Escape-Yaml([string]$s) {
    if ($null -eq $s) { return '' }
    return $s.Replace("'", "''")
}

$access = Get-EnvVar 'MINIO_ROOT_USER'
$secret = Get-EnvVar 'MINIO_ROOT_PASSWORD'
$bucket = Get-EnvVar 'MINIO_BUCKET' 'dishdive'

$yaml = @"
minio:
  host: localhost
  port: 9000
  secure: false
  accessKey: '$(Escape-Yaml $access)'
  secretKey: '$(Escape-Yaml $secret)'
  bucket: '$(Escape-Yaml $bucket)'
  publicBaseURL: http://localhost:9000
"@

Set-Content -Path $ConfigPath -Value $yaml -Encoding UTF8
Write-Host "Wrote MinIO settings into $ConfigPath (merge the 'minio:' block into your config.yaml)" -ForegroundColor Green