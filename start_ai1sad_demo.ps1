param(
    [switch]$Docs,
    [switch]$NoBackend,
    [switch]$NoFrontend,
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Frontend = Join-Path $Root "frontend"

if (-not $Python) {
    $LocalPython = "F:\Python310\python.exe"
    if (Test-Path $LocalPython) {
        $Python = $LocalPython
    } else {
        $Python = "python"
    }
}

function Stop-Port {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        if ($connection.OwningProcess) {
            Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Starting AI1SAD local demo..." -ForegroundColor Cyan

if (-not $NoBackend) {
    Stop-Port 8000
    $env:DEMO_MODE = "true"
    $env:MONGODB_URI = ""
    Start-Process -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $Root
    Write-Host "Backend:      http://127.0.0.1:8000" -ForegroundColor Green
    Write-Host "FastAPI docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
}

if (-not $NoFrontend) {
    Stop-Port 5174
    Start-Process -FilePath "npm.cmd" `
        -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "5174") `
        -WorkingDirectory $Frontend
    Write-Host "Frontend:     http://127.0.0.1:5174" -ForegroundColor Green
}

if ($Docs) {
    Stop-Port 8001
    Start-Process -FilePath $Python `
        -ArgumentList @("-m", "mkdocs", "serve", "-a", "127.0.0.1:8001") `
        -WorkingDirectory $Root
    Write-Host "MkDocs:       http://127.0.0.1:8001/AI1SAD/" -ForegroundColor Green
}

Write-Host ""
Write-Host "Demo mode is enabled for the backend. Admin writes stay disabled." -ForegroundColor Yellow
Write-Host "Close the opened server windows when you are done." -ForegroundColor Yellow
