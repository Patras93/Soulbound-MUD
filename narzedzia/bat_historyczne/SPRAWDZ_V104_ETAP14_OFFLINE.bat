@echo off
setlocal
cd /d "%~dp0..\..\"
chcp 65001 >nul
set PYTHONDONTWRITEBYTECODE=1
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 -B -m validation.v10400_suite_safe
) else (
  python -B -m validation.v10400_suite_safe
)
if ERRORLEVEL 1 (
  echo BLAD: TESTY ETAPU 14 NIE PRZESZLY. NIE WDRAZAJ.
  exit /b 1
)
echo Testy offline PASS. Nadal wymagany pelny Windows PREDEPLOY.
echo NIE WDRAZAJ bez osobnego potwierdzenia testow produkcyjnych.
exit /b 0
