@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
echo Soulbound v104 - JEDEN ZBIORCZY AUDYT, bez wdrazania.
echo Wszystkie testy dzialaja na odizolowanych danych i porcie localhost.
py -3 -u -m validation.v10400_one_archive_verify --pelny
if errorlevel 9009 python -u -m validation.v10400_one_archive_verify --pelny
set "WYNIK=%errorlevel%"
echo.
echo Wynik: %WYNIK%. Raport: RAPORT_OSTATNIEGO_AUDYTU_V104.txt
if not "%WYNIK%"=="0" echo BLAD TESTOW. NIE WDRAZAC.
echo Nawet gdy testy przejda: do produkcji wymagane sa migracja BigNumber i Windows PREDEPLOY 60/60.
pause
exit /b %WYNIK%
