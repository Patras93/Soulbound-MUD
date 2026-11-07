@echo off
setlocal
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
python -m validation.v10800_offline_suite
if errorlevel 1 goto :fail
echo V108: testy offline zakonczone. Wymagany Windows PREDEPLOY 60/60 PLUS.
exit /b 0
:fail
echo V108: REGRESJE FAIL. NIE WDRAZAC.
exit /b 1
