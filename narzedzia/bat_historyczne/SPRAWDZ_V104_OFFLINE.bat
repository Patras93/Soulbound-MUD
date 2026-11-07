@echo off
setlocal
cd /d "%~dp0..\..\"
chcp 65001 >nul
set PYTHONUTF8=1
python -m unittest validation.test_v10400_stage1
if errorlevel 1 goto fail
python -m validation.v10400_suite_safe
if errorlevel 1 goto fail
echo TESTY OFFLINE V104 PASS. To NIE jest Windows PREDEPLOY 60/60 PLUS.
exit /b 0
:fail
echo TESTY OFFLINE V104 FAIL. NIE WDRAZAJ.
exit /b 1
