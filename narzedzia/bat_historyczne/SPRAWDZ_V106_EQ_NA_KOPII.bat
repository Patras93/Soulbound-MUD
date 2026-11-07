@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0..\..\"
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
if "%~1"=="" (
 echo Podaj sciezke do prawdziwej bazy jako argument.
 echo Przykład: SPRAWDZ_V106_EQ_NA_KOPII.bat "C:\Soulbound-MUD\soulbound.db"
 exit /b 2
)
py -3 -B -m validation.v10600_kopia_realnego_eq_audyt --db "%~1"
if errorlevel 9009 python -B -m validation.v10600_kopia_realnego_eq_audyt --db "%~1"
exit /b %errorlevel%
