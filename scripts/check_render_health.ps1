# VA-10 - curl Render (or local) API /health
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
$base = $env:RENDER_HEALTH_URL
if (-not $base) {
    Write-Error "Set RENDER_HEALTH_URL in .env (e.g. https://trita-api-xxx.onrender.com)"
    exit 2
}
$base = $base.TrimEnd("/")
$uri = "$base/health"
Write-Host "GET $uri"
$response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 30
if ($response.StatusCode -ne 200) {
    Write-Error "Health check failed: $($response.StatusCode)"
    exit 1
}
Write-Host $response.Content
exit 0
