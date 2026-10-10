@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem No long-running CMD. uruchom_w_tle.py launches start_windows_bootstrap.py detached.
set "ROOT=%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
if exist "%TEMP%\" cd /d "%TEMP%" >nul 2>&1
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3 -u "%ROOT%uruchom_w_tle.py"
    exit /b %errorlevel%
)
python -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    python -u "%ROOT%uruchom_w_tle.py"
    exit /b %errorlevel%
)
echo BLAD: Wymagany Python 3.12 lub nowszy.
exit /b 2
