@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3 -u "%~dp0status_soulbound_windows.py" 2>nul
if errorlevel 1 python -u "%~dp0status_soulbound_windows.py"
echo.
pause
