@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
python -m validation.v10400_etap8_invasions_calendar
if errorlevel 1 goto fail
python -m unittest validation.test_v10400_stage1
if errorlevel 1 goto fail
echo ETAP 8 TESTY I BIGNUMBER PASS. NIE WDRAZAJ TEJ PACZKI.
exit /b 0
:fail
echo ETAP 8 FAIL. NIE WDRAZAJ.
exit /b 1
