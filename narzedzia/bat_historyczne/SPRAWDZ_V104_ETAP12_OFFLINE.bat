@echo off
setlocal
cd /d "%~dp0..\..\"
chcp 65001 >nul
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 -m validation.v10400_suite_safe
) else (
    python -m validation.v10400_suite_safe
)
if ERRORLEVEL 1 (
    echo BLAD: testy offline nie przeszly. Nie wdrazaj.
    exit /b 1
)
echo PASS: testy offline. NIE oznacza to zgody na wdrozenie.
exit /b 0
