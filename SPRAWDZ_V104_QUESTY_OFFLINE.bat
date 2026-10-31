@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONDONTWRITEBYTECODE=1
python -m validation.test_v10400_atomic_kill_quests
if errorlevel 1 (echo BLAD: atomowe zaliczanie questow. NIE WDRAZAC. & exit /b 1)
python -m validation.v10400_quest_credit_route_integrity
if errorlevel 1 (echo BLAD: trasa zaliczania questow. NIE WDRAZAC. & exit /b 1)
echo PASS: testy questow offline. NIE OZNACZA GOTOWOSCI WDROZENIA.
exit /b 0
