@echo off
setlocal
cd /d "%~dp0..\..\"
chcp 65001 >nul
set PYTHONUTF8=1
echo Soulbound v104 etap 11: testy bez polaczen TCP.
python -m validation.test_v10400_stage11_atomic
if errorlevel 1 goto fail
python -m validation.v10400_numeric_route_audit
if errorlevel 1 goto fail
python -m validation.v10400_suite_safe
if errorlevel 1 goto fail
echo ETAP 11: TESTY OFFLINE PASS. NIE JEST TO PREDEPLOY.
exit /b 0
:fail
echo ETAP 11: TESTY FAIL. NIE WDRAZAJ.
exit /b 1
