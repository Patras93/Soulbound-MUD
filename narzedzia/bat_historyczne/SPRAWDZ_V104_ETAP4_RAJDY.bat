@echo off
setlocal
cd /d "%~dp0..\..\"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
echo Soulbound MUD v104 - etap 4: testy rajdow 12-25 (bez startu serwera)
py -3 -m validation.v10400_etap4_rajdy
if errorlevel 1 goto :blad
py -3 -m validation.v10400_etap4_party_sqlite
if errorlevel 1 goto :blad
py -3 -m validation.v10300_era_raids
if errorlevel 1 goto :blad
py -3 -m validation.v10300_era_raid_party_sqlite
if errorlevel 1 goto :blad
echo PASS - testy etapu 4 i wstecznej zgodnosci zakonczone.
exit /b 0
:blad
echo FAIL - test nie powiodl sie. NIE WDRAZAC.
exit /b 1
