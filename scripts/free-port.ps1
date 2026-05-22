# Stop all processes listening on a TCP port (Windows).
# Usage: .\scripts\free-port.ps1 8000
param([Parameter(Mandatory = $true)][int]$Port)

$pids = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique)

if ($pids.Count -eq 0) {
    Write-Host "No listeners on port $Port."
    exit 0
}

Write-Host "Stopping PIDs on port ${Port}: $($pids -join ', ')"
foreach ($procId in $pids) {
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2
Write-Host "Done."
