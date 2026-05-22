# Connect + sync RM-3 beta connectors (fixtures via api_key or CONNECTOR_DEV_FIXTURES=1)
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
$env:CONNECTOR_DEV_FIXTURES = "1"
$api = if ($env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL } else { "http://127.0.0.1:8000" }
$tenant = $env:YOGA_BAR_TENANT_ID
if (-not $tenant) { Write-Error "YOGA_BAR_TENANT_ID required" }

$tokenResp = Invoke-RestMethod -Method Post -Uri "$api/dev/auth/token"
$headers = @{ Authorization = "Bearer $($tokenResp.access_token)" }

foreach ($src in @("delhivery", "meta_ads", "google_ads")) {
    Write-Host "Connect $src..."
    $body = @{ api_key = "beta-pilot"; account_ref = "yoga-bar-pilot" } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri "$api/v1/sources/$src/connect" -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "Sync $src..."
    Invoke-RestMethod -Method Post -Uri "$api/v1/sources/$src/sync" -Headers $headers
}
Write-Host "Done. Run: python scripts/run_dbt.py run"
