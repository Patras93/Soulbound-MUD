@echo off
setlocal
cd /d "%~dp0..\..\"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python -m validation.v10400_suite_safe
if errorlevel 1 (
  echo BLAD: testy regresji nie przeszly. NIE WDRAZAC.
  exit /b 1
)
echo PASS: regresja offline. TO NIE JEST ZGODA NA WDROZENIE.
echo Do pelnego wdrozenia wymagany Windows PREDEPLOY 60/60 PLUS i testy TCP.
exit /b 0
