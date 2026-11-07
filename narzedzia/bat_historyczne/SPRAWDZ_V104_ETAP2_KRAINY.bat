@echo off
setlocal
cd /d "%~dp0..\..\"
set PYTHONUTF8=1
set PYTHONDONTWRITEBYTECODE=1
py -3 -m validation.v10400_krainy_etap2
if errorlevel 1 goto bad
py -3 -m validation.v10400_etap2_integracja
if errorlevel 1 goto bad
py -3 -m unittest -q validation.test_v10400_stage1
if errorlevel 1 goto bad
echo ETAP 2 V104: TESTY PASS. Kod roboczy, NIE WDRAZAC.
exit /b 0
:bad
echo ETAP 2 V104: TESTY FAILED. NIE WDRAZAC.
exit /b 1
