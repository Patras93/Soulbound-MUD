@echo off
setlocal
cd /d "%~dp0..\..\"
chcp 65001 >nul
set PYTHONUTF8=1
python -m validation.test_v10400_stage10_numeric_safety
if errorlevel 1 goto fail
python -m validation.test_v10400_stage10_ledger
if errorlevel 1 goto fail
python -m unittest validation.test_v10400_stage1
if errorlevel 1 goto fail
python -m validation.v10400_suite_safe
if errorlevel 1 goto fail
echo ETAPY 1-10 TESTY OFFLINE PASS. NIE WDRAZAJ BEZ PELNEGO PREDEPLOY.
exit /b 0
:fail
echo TESTY V104 NIE PRZESZLY. NIE WDRAZAJ.
exit /b 1
