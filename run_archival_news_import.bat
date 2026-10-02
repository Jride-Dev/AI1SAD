@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "PAUSE_ON_EXIT=1"
for %%A in (%*) do (
    if /I "%%~A"=="--no-pause" set "PAUSE_ON_EXIT=0"
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_archival_news_import.ps1" %* --no-pause
set "EXIT_CODE=%ERRORLEVEL%"

if "%PAUSE_ON_EXIT%"=="1" (
    echo.
    echo Press any key to close this window.
    pause >nul
)

endlocal & exit /b %EXIT_CODE%
