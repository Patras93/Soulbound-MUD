@echo off
setlocal
cd /d "%~dp0..\..\"
set "PYTHONUTF8=1"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m validation.test_v10400_atomic_crafting_consumption
) else (
    python -m validation.test_v10400_atomic_crafting_consumption
)
if errorlevel 1 (
    echo BLAD: test atomowego rzemiosla NIE PRZESZEDL.
    exit /b 1
)
echo PASS: atomowe pobieranie materialow i ochrona sald.
exit /b 0
