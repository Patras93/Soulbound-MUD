@echo off
setlocal
cd /d "%~dp0..\..\"
chcp 65001 >nul
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 -m validation.v10400_suite_safe
) else (
  python -m validation.v10400_suite_safe
)
if ERRORLEVEL 1 (
  echo BLAD: ETAP 13 TESTY NIE PRZESZLY. NIE WDRAZAJ.
  exit /b 1
)
echo 44 594 kontroli offline PASS w srodowisku przygotowania.
echo Lokalny PASS nie oznacza pozwolenia na wdrozenie.
exit /b 0
