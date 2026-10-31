@echo off
setlocal
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%CD%"
echo SOULBOUND v104 - KONTROLA OFFLINE BEZ SERWERA I PORTU 4000
echo Testy nie dotykaja produkcyjnej bazy danych.
python -m validation.test_v10400_exact_reward_math || goto blad
python -m validation.test_v10400_full_kill_atomic || goto blad
python -m validation.test_v10400_atomic_kill_quests || goto blad
python -m validation.test_v10400_all_rolls_one_kill || goto blad
python -m validation.v10400_release_safety_check || goto blad
echo KONTROLE OFFLINE PASS. TO NIE JEST ZGODA NA WDROZENIE.
pause
exit /b 0
:blad
echo KONTROLA FAIL. NIE WDRAZAC.
pause
exit /b 1
