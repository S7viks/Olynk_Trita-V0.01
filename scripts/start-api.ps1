# Start Trita FastAPI locally (repo path may contain a space in Olynk_V 0.0.1)
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

Set-Location $ApiDir
pip install -e ".[dev]"
pip install -e $DltDir

$port = if ($env:TRITA_API_PORT) { $env:TRITA_API_PORT } else { "8000" }
$inUse = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($inUse) {
    $pidListen = ($inUse | Select-Object -First 1).OwningProcess
    Write-Warning "Port $port is already in use (PID $pidListen). Stop that process or run:"
    Write-Warning '  $env:TRITA_API_PORT="8001"; .\scripts\start-api.ps1'
    Write-Warning "If you change port, set SHOPIFY_REDIRECT_URI and NEXT_PUBLIC_API_URL to match."
    exit 1
}

Write-Host "Starting uvicorn on http://127.0.0.1:$port (Ctrl+C to stop)"
python -m uvicorn trita_api.main:app --reload --host 127.0.0.1 --port $port
