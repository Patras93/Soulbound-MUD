@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
set "SOURCE=%~1"
if "%SOURCE%"=="" set "SOURCE=C:\Soulbound-MUD\soulbound.db"
if not exist "%SOURCE%" (
  echo BLAD: brak bazy "%SOURCE%".
  pause
  exit /b 2
)
echo SOULBOUND V105: odczyt oryginalu i migracja w osobnej kopii TEMP.
echo Baza do odczytu: "%SOURCE%"
py -3 -u -m validation.v10500_safe_db_migration_audit --db "%SOURCE%"
if errorlevel 1 (
  echo FAIL: migracja na kopii SQLite nie przeszla.
  pause
  exit /b 1
)
echo PASS: migracja na kopii bez zmian oryginalu.
pause
exit /b 0
