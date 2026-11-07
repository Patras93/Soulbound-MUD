@echo off
setlocal
cd /d "%~dp0..\..\"
if exist "soulbound.db" (
 echo BLAD: w tym folderze znajduje sie baza postaci. Test v106 wolno uruchamiac tylko z osobnej kopii bez bazy produkcyjnej.
 exit /b 2
)
if not exist "validation\v10600_tcp_world_child.py" (
 echo BLAD: brak plikow testu TCP v106.
 exit /b 2
)
set "SOULBOUND_V106_STAGING="
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%CD%"
echo Test v106: 5 klientow na 127.0.0.1, baza i port tylko w TEMP. Nie wdrazaj tego kodu na produkcje.
py -3 -B "validation\v10600_tcp_world_smoke.py" --story
if errorlevel 1 (
 echo V106 TCP FAIL. NIE WDRAZAC.
 exit /b 1
)
echo V106 TCP STAGING PASS. To NIE jest pelny Windows PREDEPLOY.
exit /b 0
