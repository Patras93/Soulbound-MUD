@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3 -u "%ROOT%zainstaluj_predeploy.py" %*
if not errorlevel 9009 goto done
python -u "%ROOT%zainstaluj_predeploy.py" %*
:done
set "STATUS=%errorlevel%"
echo.
pause
exit /b %STATUS%
