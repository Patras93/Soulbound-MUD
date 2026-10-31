@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%CD%"
py -3 -m validation.test_v10400_big_number_copy_runtime
if errorlevel 1 (
  echo BLAD: BigNumber na kopii testowej nie przeszedl.
  exit /b 1
)
echo TEST BigNumber kopia: PASS. Nie jest to zgoda na wdrozenie v104.
endlocal
