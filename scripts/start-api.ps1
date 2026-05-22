# Start Trita FastAPI locally (repo path may contain a space in Olynk_V 0.0.1)
# Usage: .\scripts\start-api.ps1
#        .\scripts\start-api.ps1 -ReplacePort8000   # stop non-Trita app on :8000, then start
param([switch]$ReplacePort8000)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ApiDir = Join-Path $RepoRoot "trita\apps\api"
$DltDir = Join-Path $RepoRoot "trita\data\dlt"

# Load .env into process env
$EnvFile = Join-Path $RepoRoot ".env"
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
    }
}
$env:ENVIRONMENT = "development"

$jwt = $env:TRITA_JWT_SECRET
if (-not $jwt) { $jwt = $env:API_JWT_SECRET }
if (-not $jwt) { $jwt = $env:SUPABASE_JWT_SECRET }
if ($jwt -match '^sb_') {
    Write-Warning "API_JWT_SECRET/SUPABASE_JWT_SECRET looks like an sb_secret_* API key, not a JWT signing secret."
    Write-Warning "Add TRITA_JWT_SECRET=<legacy JWT secret or any 32+ char local secret> to repo .env (see .env.example)."
}

Set-Location $ApiDir
pip install -e ".[dev]"
pip install -e $DltDir
$OntologyDir = Join-Path $RepoRoot "trita\packages\ontology"
pip install -e $OntologyDir
$DecisionsDir = Join-Path $RepoRoot "trita\packages\decisions"
pip install -e $DecisionsDir

function Test-TritaHealth([string]$p) {
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:$p/health" -TimeoutSec 3
        return ($h.service -eq "trita-api")
    } catch { return $false }
}

$port = if ($env:TRITA_API_PORT) { $env:TRITA_API_PORT } else { "8000" }

if (Test-TritaHealth $port) {
    Write-Host "Trita API already listening on http://127.0.0.1:$port" -ForegroundColor Green
    exit 0
}

$listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique)

if ($listeners.Count -gt 0) {
    if ($ReplacePort8000) {
        Write-Host "Freeing port $port (PIDs: $($listeners -join ', '))..." -ForegroundColor Yellow
        foreach ($procId in $listeners) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    } else {
        Write-Warning "Port $port is in use (PIDs: $($listeners -join ', ')) and is not Trita API."
        Write-Warning "Run: .\scripts\start-api.ps1 -ReplacePort8000"
        Write-Warning "Or: `$env:TRITA_API_PORT='8001'; .\scripts\start-api.ps1 (then set NEXT_PUBLIC_API_URL=http://127.0.0.1:8001)"
        exit 1
    }
}

if (-not (Test-TritaHealth $port)) {
    $fallback = "8001"
    if ($port -ne $fallback -and -not $env:TRITA_API_PORT) {
        $busy8001 = Get-NetTCPConnection -LocalPort $fallback -State Listen -ErrorAction SilentlyContinue
        if (-not $busy8001) {
            Write-Host "Port $port still busy; using http://127.0.0.1:$fallback instead." -ForegroundColor Yellow
            Write-Host "Add to .env and trita/apps/web/.env.local: NEXT_PUBLIC_API_URL=http://127.0.0.1:$fallback"
            $port = $fallback
            $env:TRITA_API_PORT = $fallback
        }
    }
}

$webUrl = $env:NEXT_PUBLIC_WEB_URL
if ($webUrl) {
    Write-Host "Shopify OAuth callback (register in Partner Dashboard): $webUrl/api/sources/shopify/callback" -ForegroundColor Cyan
} elseif ($env:SHOPIFY_REDIRECT_URI) {
    Write-Host "Shopify OAuth callback: $($env:SHOPIFY_REDIRECT_URI)" -ForegroundColor Cyan
}

Write-Host "Starting uvicorn on http://127.0.0.1:$port (Ctrl+C to stop)"
python -m uvicorn trita_api.main:app --reload --host 127.0.0.1 --port $port
