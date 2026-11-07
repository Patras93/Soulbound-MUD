@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
py -3 -u "%~dp0narzedzia\porzadki_bat.py" %*
if errorlevel 9009 python -u "%~dp0narzedzia\porzadki_bat.py" %*
exit /b %errorlevel%
