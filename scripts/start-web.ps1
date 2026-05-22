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

# Next.js only reads .env* inside apps/web — sync NEXT_PUBLIC_* from repo root .env
$WebLocal = Join-Path $WebDir ".env.local"
if (Test-Path $EnvFile) {
    $lines = Get-Content $EnvFile | Where-Object {
        $_ -match '^\s*NEXT_PUBLIC_' -or $_ -match '^\s*#\s*(Supabase|API|Web)'
    }
    if ($lines.Count -gt 0) {
        Set-Content -Path $WebLocal -Value $lines -Encoding utf8
        Write-Host "Synced NEXT_PUBLIC_* to trita/apps/web/.env.local" -ForegroundColor DarkGray
    }
}

# Legacy filename some editors create — warn once
$LegacyEnv = Join-Path $WebDir ".ENV"
if ((Test-Path $LegacyEnv) -and -not (Test-Path $WebLocal)) {
    Write-Warning "Found trita/apps/web/.ENV - Next.js ignores it. Use .env.local (start-web.ps1 syncs from repo .env)."
}

if (-not $env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000" }
# Server-side fetch on Windows: prefer 127.0.0.1 over localhost
$env:NEXT_PUBLIC_API_URL = $env:NEXT_PUBLIC_API_URL -replace '//localhost\b', '//127.0.0.1'

$apiBase = $env:NEXT_PUBLIC_API_URL.TrimEnd('/')
try {
    $health = Invoke-RestMethod -Uri "$apiBase/health" -TimeoutSec 4
    if ($health.service -ne "trita-api") {
        Write-Warning "Port 8000 is running a different app (health: $($health | ConvertTo-Json -Compress))."
        Write-Warning "Sign-in will fail with 'Not Found' until you start Trita: .\scripts\start-api.ps1"
    }
} catch {
    Write-Warning "Trita API not reachable at $apiBase - run .\scripts\start-api.ps1 before signing in."
}

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

# Stale production .next artifacts cause 404 on main-app.js in dev — remove before dev
$NextCache = Join-Path $WebDir ".next"
if (Test-Path $NextCache) {
    $prodChunks = Join-Path $NextCache "static\chunks\main-app-*.js"
    if (Get-Item $prodChunks -ErrorAction SilentlyContinue) {
        Remove-Item -Recurse -Force $NextCache
        Write-Host "Removed stale .next (mixed build+dev cache)" -ForegroundColor DarkGray
    }
}

# npm install in apps/web breaks pnpm workspace — remove if present
$npmLock = Join-Path $WebDir "package-lock.json"
if (Test-Path $npmLock) {
    Remove-Item -Force $npmLock
    Write-Warning "Removed apps/web/package-lock.json - use pnpm from trita/ only."
}

Push-Location $WebDir
pnpm dev
