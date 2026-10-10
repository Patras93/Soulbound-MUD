@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0stop_soulbound_windows.py"
    goto :end
)
python -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    python "%~dp0stop_soulbound_windows.py"
    goto :end
)
echo BLAD: Wymagany Python 3.12 lub nowszy.
set "RESULT=2"
goto :finish
:end
set "RESULT=%errorlevel%"
:finish
echo Nacisnij dowolny klawisz, aby zamknac okno STOP.
pause >nul
exit /b %RESULT%
