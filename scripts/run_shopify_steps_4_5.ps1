# Steps 4-5: requires API on :8000 and Yoga Bar tenant_id in .env as YOGA_BAR_TENANT_ID
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}

$tenantId = $env:YOGA_BAR_TENANT_ID
if (-not $tenantId) {
    Write-Host "Set YOGA_BAR_TENANT_ID in .env (from Supabase: select id from tenants where slug='yoga-bar')"
    exit 1
}

$api = $env:NEXT_PUBLIC_API_URL
if (-not $api) { $api = "http://localhost:8000" }

Write-Host "Step 4 — open in browser:"
$shop = if ($env:YOGA_BAR_SHOP_DOMAIN) { ($env:YOGA_BAR_SHOP_DOMAIN -replace '\.myshopify\.com$','') } else { 'tritabyolynk' }
Write-Host "$api/dev/shopify/go?tenant_id=$tenantId&shop=$shop"
Write-Host ""
Write-Host "After Shopify approves, run step 5:"
Write-Host "python scripts/shopify_sync_only.py"
