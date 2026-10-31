@echo off
setlocal
cd /d "%~dp0"
py -3 validation\v10400_suite_safe.py
if errorlevel 1 (
  echo BLAD: testy v104 NIE PRZESZLY.
  exit /b 1
)
echo PASS: kontrola offline skonczona.
exit /b 0
