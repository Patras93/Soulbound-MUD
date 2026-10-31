@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
python -m validation.test_v10400_all_rolls_one_kill
if errorlevel 1 (echo BLAD: zestaw lupow jednego zabicia. NIE WDRAZAC. & exit /b 1)
python -m validation.test_v10400_party_loot_atomic
if errorlevel 1 (echo BLAD: lup druzynowy. NIE WDRAZAC. & exit /b 1)
python -m validation.v10400_party_loot_route_integrity
if errorlevel 1 (echo BLAD: trasa lupow. NIE WDRAZAC. & exit /b 1)
echo PASS: transakcje lupow offline. NIE OZNACZA gotowosci produkcyjnej.
exit /b 0
