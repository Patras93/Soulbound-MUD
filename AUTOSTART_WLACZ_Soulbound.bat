@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
  py -3 -u "%~dp0windows_autostart.py" install
  goto :end
)
python -u "%~dp0windows_autostart.py" install
goto :end
:end
set "RESULT=%errorlevel%"
echo.
echo Nacisnij klawisz aby zamknac.
pause >nul
exit /b %RESULT%
