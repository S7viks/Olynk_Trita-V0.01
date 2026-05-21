# Local dev health — API (+ optional LiteLLM)
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

$apiBase = if ($env:RENDER_HEALTH_URL) { $env:RENDER_HEALTH_URL } elseif ($env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL } else { "http://127.0.0.1:8000" }
$apiBase = $apiBase.TrimEnd("/")

Write-Host "API health: $apiBase/health"
& (Join-Path $RepoRoot "scripts\check_render_health.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$litellm = $env:LITELLM_PROXY_URL
if ($litellm) {
    $litellm = $litellm.TrimEnd("/")
    Write-Host "LiteLLM: $litellm/health/liveliness"
    try {
        $r = Invoke-WebRequest -Uri "$litellm/health/liveliness" -UseBasicParsing -TimeoutSec 5
        Write-Host "  OK ($($r.StatusCode))"
    } catch {
        Write-Host "  SKIP — LiteLLM not running (start .\scripts\start-litellm.ps1)" -ForegroundColor Yellow
    }
}

Write-Host "Local dev health OK"
exit 0
