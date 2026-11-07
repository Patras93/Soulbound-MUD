@echo off
setlocal
cd /d "%~dp0..\..\"
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
echo Soulbound v104 - TEST walut BigNumber tylko na kopii SQLite TEMP.
echo Ten test NIE otwiera serwera ani bazy produkcyjnej.
py -3 -m unittest -v validation.test_v10400_currency_big_number_copy
if errorlevel 9009 python -m unittest -v validation.test_v10400_currency_big_number_copy
set "WYNIK=%errorlevel%"
if not "%WYNIK%"=="0" echo TEST FAIL - NIE WDRAZAC.
if "%WYNIK%"=="0" echo TEST KOPII PASS - nadal NIE WDRAZAC.
pause
exit /b %WYNIK%
