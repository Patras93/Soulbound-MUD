@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%CD%"
python -m validation.v10400_release_gate --timeout 150
if errorlevel 1 (echo TESTY NIEPRZESZLY - NIE WDRAZAC & exit /b 1)
echo TESTY OFFLINE PASS. WERSJA NADAL NIE JEST FINAL.
exit /b 0
