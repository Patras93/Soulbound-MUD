@echo off
setlocal
cd /d "%~dp0..\..\"
if not exist logs mkdir logs
set "PYTHONDONTWRITEBYTECODE=1"
set "SOULBOUND_HOST=127.0.0.1"
set "SOULBOUND_ULTRA_SOURCE_DB=C:\Soulbound-MUD\soulbound.db"
py -3 -B -m validation.v10700_eq_routes_on_real_backup --db "%SOULBOUND_ULTRA_SOURCE_DB%" > logs\AUDYT_V107_EQ_TRANSAKCJE_WINDOWS.log 2>&1
set "SB_CODE=%ERRORLEVEL%"
type logs\AUDYT_V107_EQ_TRANSAKCJE_WINDOWS.log
if not "%SB_CODE%"=="0" echo V107 EQ TRANSAKCJE: FAIL, kod %SB_CODE%.
if "%SB_CODE%"=="0" echo V107 EQ TRANSAKCJE: 21 kontroli PASS na KOPII, NIE pozwala na wdrozenie.
exit /b %SB_CODE%
