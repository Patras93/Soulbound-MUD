@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONDONTWRITEBYTECODE=1
python -m validation.v10400_suite_safe
if errorlevel 1 (
  echo FAIL: testy v104 nie przeszly. NIE WDRAZAC.
  exit /b 1
)
echo PASS: offline. To NIE jest zgoda na wdrozenie.
echo Wymagane: BigNumber TEXT, Windows PREDEPLOY oraz testy realnej gry TCP.
exit /b 0
