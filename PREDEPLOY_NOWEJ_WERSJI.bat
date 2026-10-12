@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
  py -3 -u "%ROOT%predeploy_nowej_wersji.py" %*
  goto done
)
python -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
  python -u "%ROOT%predeploy_nowej_wersji.py" %*
  goto done
)
echo BLAD: Python 3.12 lub nowszy jest wymagany.
set "STATUS=2"
goto pause
:done
set "STATUS=%errorlevel%"
:pause
echo.
echo Wynik PREDEPLOY: %STATUS% (0 oznacza PASS).
pause
exit /b %STATUS%
