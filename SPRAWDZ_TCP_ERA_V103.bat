@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [Soulbound Era Bez Granic] TEST TCP NA PRYWATNEJ KOPII TESTOWEJ
 echo Dwa fikcyjne konta, port localhost, prywatna SQLite. Bez zmian serwera produkcyjnego.
python -u -m validation.v10300_era_tcp_smoke
if errorlevel 1 (
  echo NIEZALICZONE: test TCP zakonczyl sie bledem. Nie wdrazaj wersji roboczej.
  pause
  exit /b 1
)
echo TEST TCP ZALICZONY. Nie zastepuje pelnego PREDEPLOY 60/60 PLUS.
pause
