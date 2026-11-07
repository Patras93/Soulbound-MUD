@echo off
setlocal
cd /d "%~dp0..\..\"
set "PYTHONDONTWRITEBYTECODE=1"
set "SOULBOUND_DB="
set "SOULBOUND_PORT="
set "DATABASE_URL="
set "PORT="
python -B -m unittest -q validation.test_v10400_class_xp_big_number_copy validation.test_v10400_character_multi_axis_copy validation.test_v10400_real_character_big_number_rehearsal validation.test_v10400_big_number_copy_runtime
if errorlevel 1 (
  echo BLAD: Testy kopii BigNumber nie przeszly. NIE WDRAZAC.
  exit /b 1
)
echo PASS: testowy BigNumber dla klas i 14 osi postaci.
echo UWAGA: to jest wersja robocza do testow offline, NIE WDRAZAC.
endlocal
