@echo off
setlocal
cd /d "%~dp0..\..\"
set PYTHONDONTWRITEBYTECODE=1
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m validation.v10400_suite_safe
) else (
    python -m validation.v10400_suite_safe
)
set EXIT_CODE=%errorlevel%
if not "%EXIT_CODE%"=="0" (
    echo BLAD: testy V104 nie przeszly. Nie wdrazaj paczki.
) else (
    echo PASS: bezpieczne testy offline V104.
    echo Uwaga: to NIE jest potwierdzenie gotowosci produkcyjnej ani test TCP 4000.
)
echo Nacisnij dowolny klawisz, aby zamknac okno.
pause >nul
exit /b %EXIT_CODE%
