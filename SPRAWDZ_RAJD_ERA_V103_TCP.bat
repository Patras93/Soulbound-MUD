@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo SOULBOUND ERA BEZ GRANIC - TEST RAJDU TCP NA PRYWATNEJ KOPII
echo 2 fikcyjne konta, 3 bossow, zadania NPC i nagrody.
echo Test uzywa tylko 127.0.0.1, wolnego portu i osobnej bazy SQLite.
echo Uprawnienia admina istnieja wylacznie na koncie serwera testowego.
echo Nie wprowadza zadnych zmian na serwerze produkcyjnym.
python -u -m validation.v10300_era_tcp_raid_journey
if errorlevel 1 (
  echo TEST NIEZALICZONY. Zachowaj wynik bledu do analizy.
  echo PACZKA ROBOCZA - NIE WDRAZAC.
  pause
  exit /b 1
)
echo TEST RAJDU TCP ZALICZONY.
echo To test trzech zaliczen przy wykorzystaniu admin cios wyrok.
echo Nie zastepuje testu faz walki ani Windows PREDEPLOY 60/60 PLUS.
pause
