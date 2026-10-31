@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3 -m unittest -v validation.test_v10400_stage1
if errorlevel 1 (
  echo V104 ETAP1: BLAD TESTOW. NIE WDRAZAC.
  pause
  exit /b 1
)
echo V104 ETAP1: TESTY JEDNOSTKOWE PASS. TO NADAL PACZKA ROBOCZA.
echo Audyt kopii SQLite: py -3 -m validation.v10400_big_number_audit --db "SCIEZKA_DO_KOPII.db"
echo Proba migracji: py -3 -m validation.v10400_migration_rehearsal --db "SCIEZKA_DO_KOPII.db"
pause
