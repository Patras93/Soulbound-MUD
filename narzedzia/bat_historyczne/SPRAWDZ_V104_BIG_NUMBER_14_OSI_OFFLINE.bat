@echo off
setlocal
cd /d "%~dp0..\..\"
set "PYTHONDONTWRITEBYTECODE=1"
set "SOULBOUND_DB="
set "SOULBOUND_PORT="
set "DATABASE_URL="
set "PORT="
python -B -m unittest -q validation.test_v10400_character_multi_axis_copy validation.test_v10400_real_character_big_number_rehearsal validation.test_v10400_big_number_copy_runtime
if errorlevel 1 (
 echo BLAD: test 14 osi BigNumber nie przeszedl. NIE WDRAZAC.
 exit /b 1
)
echo PASS: testowe 14 osi rozwoju i zabezpieczenia zapisu.
echo UWAGA: dotyczy WYLACZNIE odizolowanej kopii bazy. NIE WDRAZAC.
endlocal
