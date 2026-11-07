@echo off
setlocal
cd /d "%~dp0..\..\"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
set "SOULBOUND_DB="
set "SOULBOUND_PORT="
set "DATABASE_URL="
set "PORT="
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m unittest -q validation.test_v10400_player_profile_current validation.test_v10400_work_xp_big_number_copy validation.test_v10400_class_xp_big_number_copy
) else (
  python -m unittest -q validation.test_v10400_player_profile_current validation.test_v10400_work_xp_big_number_copy validation.test_v10400_class_xp_big_number_copy
)
if errorlevel 1 goto fail
echo PROFILE + BIGNUMBER PRACA: PASS (tylko testy offline).
echo Pakiet nadal NIE jest gotowy do produkcji.
exit /b 0
:fail
echo TESTY NIE PRZESZLY. NIE WDRAZAC.
exit /b 1
