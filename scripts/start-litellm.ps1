# Start LiteLLM proxy locally (P-LLM-PROXY) - Windows-safe (asyncio, not uvloop)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$LitellmDir = Join-Path $RepoRoot "trita\services\litellm"
$EnvFile = Join-Path $RepoRoot ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
        }
    }
}

if (-not $env:GEMINI_API_KEY) {
    Write-Warning "GEMINI_API_KEY not set - gemini-cards will fail until .env is filled."
}
if (-not $env:LITELLM_MASTER_KEY) {
    Write-Warning "LITELLM_MASTER_KEY not set - use any random string in .env (must match API requests)."
}

$Python = "python"
if (Test-Path "C:\Python312\python.exe") {
    $Python = "C:\Python312\python.exe"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $py312 = py -3.12 -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $py312) { $Python = $py312.Trim() }
}

$port = if ($env:LITELLM_PORT) { $env:LITELLM_PORT } else { "4000" }
$inUse = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($inUse) {
    $pidListen = ($inUse | Select-Object -First 1).OwningProcess
    Write-Warning "Port $port is already in use (PID $pidListen). Stop it or set LITELLM_PORT."
    exit 1
}
$ReqFile = Join-Path $LitellmDir "requirements.txt"

Write-Host "LiteLLM deps ($Python)..." -ForegroundColor DarkGray
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $Python -m pip install -r $ReqFile -q 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { $ErrorActionPreference = $prevEap; exit $LASTEXITCODE }

& $Python -m pip show litellm 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing litellm (proxy)..." -ForegroundColor DarkGray
    & $Python -m pip install "litellm[proxy]>=1.55.0" -q 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        & $Python -m pip install "litellm>=1.55.0" -q 2>&1 | Out-Null
    }
}
$ErrorActionPreference = $prevEap

# Local proxy does not need LiteLLM's Prisma DB; Supabase DATABASE_URL in .env breaks startup.
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:DIRECT_URL -ErrorAction SilentlyContinue

$env:LITELLM_CONFIG_FILE = Join-Path $LitellmDir "config.yaml"
$env:LITELLM_HOST = "127.0.0.1"
$env:LITELLM_PORT = $port

$ProxyScript = Join-Path $RepoRoot "scripts\run_litellm_proxy.py"
Write-Host "Starting LiteLLM on http://127.0.0.1:$port (Ctrl+C to stop)"
Set-Location $LitellmDir
& $Python $ProxyScript
