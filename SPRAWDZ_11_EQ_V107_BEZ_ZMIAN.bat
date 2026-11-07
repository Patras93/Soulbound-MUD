@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
echo SOULBOUND v108 - kontrola 11 brakow starego EQ v107
 echo Produkcja i backup beda tylko odczytywane. Brak zmian w bazie.
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m validation.v10800_eq107_readonly_reconcile --root "C:\Soulbound-MUD"
) else (
    python -m validation.v10800_eq107_readonly_reconcile --root "C:\Soulbound-MUD"
)
echo.
echo Skopiuj wynik tego okna do rozmowy. Nie wdrazaj v108.
pause
