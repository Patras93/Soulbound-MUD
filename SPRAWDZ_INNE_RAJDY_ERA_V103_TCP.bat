@echo off
setlocal
cd /d "%~dp0"
echo SOULBOUND ERA V103 - TEST RAJDOW NA PRYWATNYM SERWERZE TCP.
echo Domyslnie: Wulkany Wiecznych Kuzni i Morze Zerwanych Gwiazd.
echo Wszystkie krainy: SPRAWDZ_INNE_RAJDY_ERA_V103_TCP.bat --regions all
echo.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m validation.v10300_era_tcp_other_raids %*
) else (
  python -m validation.v10300_era_tcp_other_raids %*
)
set "ERR=%ERRORLEVEL%"
echo.
if "%ERR%"=="0" (echo TEST RAJDOW TCP: PASS) else (echo TEST RAJDOW TCP: BLAD - kod %ERR%)
pause
exit /b %ERR%
