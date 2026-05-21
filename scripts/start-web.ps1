# Start Next.js web app (T-P0-040)
# Usage: .\scripts\start-web.ps1
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$WebDir = Join-Path $RepoRoot "trita\apps\web"
$EnvFile = Join-Path $RepoRoot ".env"

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
        }
    }
}

if (-not $env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000" }

Push-Location (Join-Path $RepoRoot "trita")
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing pnpm dependencies..." -ForegroundColor Cyan
    pnpm install
}
Pop-Location

Write-Host ""
Write-Host "Trita web: http://localhost:3000" -ForegroundColor Cyan
$apiUrl = $env:NEXT_PUBLIC_API_URL
Write-Host "  API: $apiUrl" -ForegroundColor DarkGray
Write-Host ""

Push-Location $WebDir
pnpm dev
