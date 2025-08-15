# Generates strong MINIO_ROOT_USER and MINIO_ROOT_PASSWORD and writes them to .env
param(
    [string]$EnvPath,
    [int]$UserLength = 20,
    [int]$PasswordLength = 40
)

if (-not $EnvPath) {
    $repoRoot = (Resolve-Path -Path (Join-Path -Path $PSScriptRoot -ChildPath '..\..')).Path
    $EnvPath = Join-Path -Path $repoRoot -ChildPath '.env'
}

function New-RandomString {
    param(
        [int]$Length,
        [string]$Charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._'
    )
    $bytes = New-Object 'System.Byte[]' ($Length)
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $chars = @()
    $max = $Charset.Length
    foreach ($b in $bytes) {
        $chars += $Charset[ $b % $max ]
    }
    -join $chars
}

$rootUser = New-RandomString -Length $UserLength
$rootPass = New-RandomString -Length $PasswordLength

$envLines = @(
    "MINIO_ROOT_USER=$rootUser",
    "MINIO_ROOT_PASSWORD=$rootPass",
    "MINIO_BUCKET=dishdive"
)

Set-Content -Path $EnvPath -Value ($envLines -join [Environment]::NewLine) -NoNewline -Encoding UTF8
Write-Host "Wrote MinIO secrets to $EnvPath" -ForegroundColor Green
