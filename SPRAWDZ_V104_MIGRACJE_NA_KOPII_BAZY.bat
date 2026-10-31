@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%"
set "PYTHONDONTWRITEBYTECODE=1"
if "%~1"=="" (
  echo SOULBOUND v104 - proba BigNumber TYLKO NA KOPII.
  echo Podaj sciezke SQLite jako argument, np.:
  echo SPRAWDZ_V104_MIGRACJE_NA_KOPII_BAZY.bat "C:\Soulbound-MUD\soulbound.db"
  echo Skrypt odczytuje zrodlo w trybie tylko do odczytu i wykonuje migracje w TEMP.
  exit /b 2
)
set "RAPORT=%USERPROFILE%\Downloads\SOULBOUND_V104_PROBA_MIGRACJI_PL.txt"
py -3 -m validation.v10400_migration_rehearsal --db "%~1" > "%RAPORT%" 2>&1
set "RESULT=%ERRORLEVEL%"
type "%RAPORT%"
if not "%RESULT%"=="0" (
  echo NIEZALICZONE: nie wdrazac v104.
) else (
  echo Test kopii zakonczony. To NIE jest zgoda na wdrozenie.
)
echo Raport: %RAPORT%
endlocal & exit /b %RESULT%
