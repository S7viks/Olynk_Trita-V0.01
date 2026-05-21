# Start Trita local dev stack (API; optional LiteLLM hint)
# Usage: .\scripts\start-local.ps1
# Docs: docs/LOCAL-DEV.md
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env"

if (-not (Test-Path $EnvFile)) {
    Write-Host "Missing .env — copy from .env.example first:" -ForegroundColor Yellow
    Write-Host "  Copy-Item .env.example .env"
    exit 1
}

Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
    }
}

if (-not $env:DATABASE_URL) {
    Write-Error "DATABASE_URL not set in .env (Supabase pooler URL required)"
}
if (-not $env:SUPABASE_JWT_SECRET -and -not $env:API_JWT_SECRET) {
    Write-Error "SUPABASE_JWT_SECRET or API_JWT_SECRET required in .env"
}

# Local defaults so health scripts and OAuth redirects work without Render/Fly
if (-not $env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000" }
if (-not $env:RENDER_HEALTH_URL) { $env:RENDER_HEALTH_URL = $env:NEXT_PUBLIC_API_URL }
$env:ENVIRONMENT = "development"

$port = if ($env:TRITA_API_PORT) { $env:TRITA_API_PORT } else { "8000" }
$apiBase = "http://127.0.0.1:$port"

Write-Host ""
Write-Host "Trita local dev" -ForegroundColor Cyan
Write-Host "  API:     $apiBase"
Write-Host "  Health:  $apiBase/health"
Write-Host "  Docs:    $apiBase/docs"
Write-Host ""

if ($env:LITELLM_PROXY_URL -and $env:GEMINI_API_KEY) {
    Write-Host "LiteLLM: start in a second terminal if you need live LLM drafts:" -ForegroundColor DarkGray
    Write-Host "  .\scripts\start-litellm.ps1"
    Write-Host ""
} else {
    Write-Host "LiteLLM: skipped (set LITELLM_PROXY_URL + GEMINI_API_KEY for /v1/llm/draft)" -ForegroundColor DarkGray
    Write-Host ""
}

& (Join-Path $RepoRoot "scripts\start-api.ps1")
