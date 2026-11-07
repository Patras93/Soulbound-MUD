@echo off
setlocal
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
cd /d "%~dp0..\..\"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m unittest -q validation.test_v10400_concurrent_kill_sqlite validation.test_v10400_deferred_commit_rollback
) else (
  python -m unittest -q validation.test_v10400_concurrent_kill_sqlite validation.test_v10400_deferred_commit_rollback
)
if errorlevel 1 (
  echo BLEDY: testy wspolnych nagrod SQLite. NIE WDRAZAC.
  exit /b 1
)
echo PASS: wspolne SAVEPOINT, dwie walki, wycofanie i anulowanie.
echo UWAGA: to nie jest pelny Windows PREDEPLOY ani test BigNumber.
exit /b 0
