@echo off
setlocal
cd /d "%~dp0..\..\"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%CD%"
python -m validation.v10400_release_gate --timeout 150
if errorlevel 1 (
  echo TESTY FAIL - NIE WDRAZAC
  pause
  exit /b 1
)
echo TESTY OFFLINE PASS - NADAL NIE WDRAZAC, BRAK WINDOWS PREDEPLOY I BIG NUMBER.
pause
exit /b 0
