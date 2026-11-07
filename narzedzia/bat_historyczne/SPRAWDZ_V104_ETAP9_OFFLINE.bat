@echo off
setlocal
cd /d "%~dp0..\..\"
chcp 65001 >nul
set PYTHONUTF8=1
python -m validation.v10400_etap9_invasion_rewards
if errorlevel 1 goto fail
python -m validation.v10400_suite_safe
if errorlevel 1 goto fail
python -m unittest validation.test_v10400_stage1
if errorlevel 1 goto fail
echo ETAPY 1-9 OFFLINE PASS. Nie wdrazaj bez Windows PREDEPLOY.
exit /b 0
:fail
echo V104 OFFLINE FAIL. NIE WDRAZAJ.
exit /b 1
