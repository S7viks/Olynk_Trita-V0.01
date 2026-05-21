# Start LiteLLM proxy locally (P-LLM-PROXY)
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
$port = if ($env:LITELLM_PORT) { $env:LITELLM_PORT } else { "4000" }
pip install "litellm[proxy]>=1.55.0" -q
Set-Location $LitellmDir
Write-Host "Starting LiteLLM on http://127.0.0.1:$port"
litellm --config config.yaml --host 127.0.0.1 --port $port
