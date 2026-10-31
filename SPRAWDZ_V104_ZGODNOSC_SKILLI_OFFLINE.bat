@echo off
setlocal
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
set "PYTHONPATH=%CD%"
echo Soulbound v104 - 5461 historycznych + 66 nowych umiejetnosci.
python -c "from validation.v1110_unique_skill_names import run_regression; run_regression()"
if errorlevel 1 goto failed
python -m unittest -q validation.test_v10400_skill_catalog_rc
if errorlevel 1 goto failed
python -m validation.v10400_release_gate --timeout 120
if errorlevel 1 goto failed
echo.
echo TEST OFFLINE PASS. TO NIE JEST ZGODA NA WDROZENIE.
pause
exit /b 0
:failed
echo.
echo TEST FAIL. NIE WDRAZAC.
pause
exit /b 1
