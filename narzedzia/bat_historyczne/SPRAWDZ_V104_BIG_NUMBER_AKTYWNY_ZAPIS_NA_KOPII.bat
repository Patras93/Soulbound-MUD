@echo off
setlocal
cd /d "%~dp0..\..\"
set "PYTHONDONTWRITEBYTECODE=1"
set "SOULBOUND_DB="
set "SOULBOUND_PORT="
set "DATABASE_URL="
set "PORT="
python -B -m unittest -v validation.test_v10400_real_character_big_number_rehearsal
if errorlevel 1 (
 echo BLAD: test BigNumber v104 nie przeszedl. NIE WDRAZAC.
 exit /b 1
)
echo PASS: izolowany zapis BigNumber przez rzeczywiste metody postaci.
echo UWAGA: To test na prywatnej bazie, NIE migracja produkcyjna.
endlocal
