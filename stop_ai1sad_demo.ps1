param(
    [int[]]$Ports = @(8000, 5174, 8001)
)

$ErrorActionPreference = "Stop"

foreach ($port in $Ports) {
    Write-Host "Checking port $port..." -ForegroundColor Cyan
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    $processIds = $connections | Where-Object { $_.OwningProcess } | Select-Object -ExpandProperty OwningProcess -Unique

    if (-not $processIds) {
        Write-Host "No process is bound to port $port." -ForegroundColor DarkGray
        continue
    }

    foreach ($processId in $processIds) {
        try {
            $process = Get-Process -Id $processId -ErrorAction Stop
            Write-Host "Stopping $($process.ProcessName) on port $port (PID $processId)..." -ForegroundColor Yellow
            Stop-Process -Id $processId -Force -ErrorAction Stop
        } catch {
            Write-Host "Could not stop PID $processId on port ${port}: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host "AI1SAD demo stop request complete." -ForegroundColor Green
