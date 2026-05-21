# Local dev health - API (+ optional LiteLLM)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
        }
    }
}

# Local dev: prefer NEXT_PUBLIC_API_URL; do not use remote RENDER_HEALTH_URL for this script
$apiBase = if ($env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL } else { "http://127.0.0.1:8000" }
$apiBase = $apiBase.TrimEnd("/")

$apiHealthUri = "$apiBase/health"
Write-Host "API health: $apiHealthUri"
try {
    $apiResp = Invoke-WebRequest -Uri $apiHealthUri -UseBasicParsing -TimeoutSec 10
    if ($apiResp.StatusCode -ne 200) {
        Write-Error "API health failed: $($apiResp.StatusCode)"
        exit 1
    }
    Write-Host "  OK ($($apiResp.StatusCode))"
} catch {
    Write-Host "  FAIL - start API: .\scripts\start-local.ps1" -ForegroundColor Red
    exit 1
}

$litellm = $env:LITELLM_PROXY_URL
if ($litellm) {
    $litellm = $litellm.TrimEnd("/")
    Write-Host "LiteLLM: $litellm/health/liveliness"
    try {
        $r = Invoke-WebRequest -Uri "$litellm/health/liveliness" -UseBasicParsing -TimeoutSec 5
        Write-Host "  OK ($($r.StatusCode))"
    } catch {
        Write-Host "  SKIP - LiteLLM not running (start .\scripts\start-litellm.ps1)" -ForegroundColor Yellow
    }
}

Write-Host "Local dev health OK"
exit 0
