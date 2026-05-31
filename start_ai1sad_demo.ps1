param(
    [switch]$NoBackend,
    [switch]$NoFrontend,
    [switch]$NoDocs,
    [switch]$NoBrowser,
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Frontend = Join-Path $Root "frontend"

function Test-PortInUse {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return [bool]$connections
}

function Resolve-PythonCommand {
    if ($Python) {
        return $Python
    }

    if ($env:WSL_DISTRO_NAME) {
        return "python3"
    }

    $localPython = "F:\Python310\python.exe"
    if (Test-Path $localPython) {
        return $localPython
    }

    $python3 = Get-Command "python3" -ErrorAction SilentlyContinue
    if ($python3) {
        return "python3"
    }

    return "python"
}

function Start-ServerWindow {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command
    )

    $quotedTitle = $Title.Replace("'", "''")
    $commandText = "Set-Location -LiteralPath '$WorkingDirectory'; `$Host.UI.RawUI.WindowTitle = '$quotedTitle'; $Command"
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $commandText)
}

function Warn-Or-Start {
    param(
        [int]$Port,
        [string]$Name,
        [scriptblock]$StartAction
    )

    if (Test-PortInUse -Port $Port) {
        Write-Host "$Name port $Port is already in use. Not starting $Name." -ForegroundColor Yellow
        Write-Host "Run .\stop_ai1sad_demo.bat to stop AI1SAD demo ports, or close the process using that port." -ForegroundColor Yellow
        return
    }

    & $StartAction
}

$pythonCommand = Resolve-PythonCommand

Write-Host "Starting AI1SAD local demo..." -ForegroundColor Cyan
Write-Host "Repo root: $Root" -ForegroundColor DarkCyan

if (-not $NoBackend) {
    Write-Host "Starting backend..." -ForegroundColor Cyan
    Warn-Or-Start -Port 8000 -Name "Backend" -StartAction {
        $backendCommand = "`$env:DEMO_MODE='true'; `$env:MONGODB_URI=''; & '$pythonCommand' -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
        Start-ServerWindow -Title "AI1SAD Backend :8000" -WorkingDirectory $Root -Command $backendCommand
        Write-Host "Backend:      http://localhost:8000" -ForegroundColor Green
        Write-Host "FastAPI docs: http://localhost:8000/docs" -ForegroundColor Green
    }
}

if (-not $NoFrontend) {
    Write-Host "Starting frontend..." -ForegroundColor Cyan
    Warn-Or-Start -Port 5174 -Name "Frontend" -StartAction {
        Start-ServerWindow -Title "AI1SAD Frontend :5174" -WorkingDirectory $Frontend -Command "npm run dev -- --host 0.0.0.0 --port 5174"
        Write-Host "Frontend:     http://localhost:5174" -ForegroundColor Green
    }
}

if (-not $NoDocs) {
    Write-Host "Starting MkDocs..." -ForegroundColor Cyan
    Warn-Or-Start -Port 8001 -Name "MkDocs" -StartAction {
        Start-ServerWindow -Title "AI1SAD MkDocs :8001" -WorkingDirectory $Root -Command "mkdocs serve --dev-addr 0.0.0.0:8001"
        Write-Host "MkDocs:       http://localhost:8001" -ForegroundColor Green
    }
}

if (-not $NoBrowser) {
    Write-Host "Opening browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:5174"
    Start-Process "http://localhost:8000/docs"
    Start-Process "http://localhost:8001"
}

Write-Host ""
Write-Host "AI1SAD demo launch requested. Server windows stay open while services run." -ForegroundColor Yellow
Write-Host "Use .\stop_ai1sad_demo.bat when you are done." -ForegroundColor Yellow
