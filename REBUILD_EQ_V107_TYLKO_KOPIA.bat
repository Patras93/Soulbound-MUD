@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
echo Soulbound v108 - REBUILD EQ na odlaczonej kopii. NIE WDRAZAC.
echo C:\Soulbound-MUD i oryginalny backup sa tylko odczytywane.
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m validation.v10800_eq_rebuild_copy --root "C:\Soulbound-MUD" > WYNIK_REBUILD_EQ.txt 2>&1
) else (
  python -m validation.v10800_eq_rebuild_copy --root "C:\Soulbound-MUD" > WYNIK_REBUILD_EQ.txt 2>&1
)
type WYNIK_REBUILD_EQ.txt
echo.
echo Przeslij TYLKO plik WYNIK_REBUILD_EQ.txt. Nie przesylaj bazy SQLite.
echo NIE WDRAZAJ REBUILT_TEST_ONLY.sqlite na serwerze.
pause
