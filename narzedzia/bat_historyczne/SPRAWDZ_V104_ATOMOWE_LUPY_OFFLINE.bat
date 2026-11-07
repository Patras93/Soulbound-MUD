@echo off
setlocal
cd /d "%~dp0..\..\"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python -m validation.test_v10400_party_loot_atomic
if errorlevel 1 (echo BLAD: testy łupow. NIE WDRAZAC. & exit /b 1)
python -m validation.v10400_party_loot_route_integrity
if errorlevel 1 (echo BLAD: audyt trasy łupow. NIE WDRAZAC. & exit /b 1)
echo PASS: łupy drużynowe offline. Nie oznacza gotowosci produkcyjnej.
exit /b 0
