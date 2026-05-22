# Upload Yoga Bar Tally unit-cost fixture via CSV hub
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Fixture = Join-Path $RepoRoot "trita\data\dlt\src\trita_dlt\fixtures\tally_unit_cost_yoga_bar.csv"
$EnvFile = Join-Path $RepoRoot ".env"
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
    }
}
$api = if ($env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL } else { "http://127.0.0.1:8000" }
$tokenResp = Invoke-RestMethod -Method Post -Uri "$api/dev/auth/token"
$headers = @{ Authorization = "Bearer $($tokenResp.access_token)" }
Write-Host "Uploading $Fixture ..."
$token = $tokenResp.access_token
$resultJson = curl.exe -s -X POST "$api/v1/csv/upload" `
    -H "Authorization: Bearer $token" `
    -F "file=@$Fixture;type=text/csv" `
    -F "logical_source=tally"
$result = $resultJson | ConvertFrom-Json
$result | Format-List
Write-Host "Run: python scripts/run_dbt.py run"
