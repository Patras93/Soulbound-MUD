@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%CD%"
echo TEST WYŁACZNIE NA KOPII, PRYWATNY PORT TCP I PRYWATNA BAZA.
python -m validation.v10400_tcp_full_journey
if errorlevel 1 (
  echo TEST TCP NIE PRZESZEDL. NIE WDRAZAC.
  pause
  exit /b 1
)
echo TEST TCP PASS. TO NIE JEST PELNY WINDOWS PREDEPLOY.
pause
exit /b 0
