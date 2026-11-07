@echo off
if exist "%~dp0validation\v10700_magitek_regression.py" (
  echo v107 MAGITEK: KOD ROBOCZY, NIE WDRAZAC.
  exit /b 2
)
if exist "%~dp0validation\v10600_tcp_world_smoke.py" (
  echo WERSJA ROBOCZA v106. WDROZENIE ZABLOKOWANE.
  exit /b 2
)
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3 -u "%ROOT%wdroz_po_predeploy.py"
if not errorlevel 9009 goto done
python -u "%ROOT%wdroz_po_predeploy.py"
:done
set "STATUS=%errorlevel%"
echo.
echo Wynik wdrozenia: %STATUS%
pause
exit /b %STATUS%
