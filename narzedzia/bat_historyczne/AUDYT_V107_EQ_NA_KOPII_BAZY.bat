@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0..\..\"
if "%~1"=="" (
  set "SOURCE_DB=C:\Soulbound-MUD\soulbound.db"
) else (
  set "SOURCE_DB=%~f1"
)
if not exist "%~dp0..\..\logs" mkdir "%~dp0..\..\logs"
set "SB_LOG=%~dp0..\..\logs\AUDYT_V107_EQ_WINDOWS.log"
python -u -m validation.v10700_eq_ledger_live_clone --db "%SOURCE_DB%" > "%SB_LOG%" 2>&1
set "SB_CODE=%ERRORLEVEL%"
type "%SB_LOG%"
echo.
echo LOG: %SB_LOG%
echo WYNIK AUDYTU EQ: %SB_CODE% - nigdy nie daje zgody na wdrozenie.
pause
exit /b %SB_CODE%
