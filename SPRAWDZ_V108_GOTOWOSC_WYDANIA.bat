@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
where py >nul 2>nul
if errorlevel 1 goto python
py -3 -B -u -m validation.v10800_release_readiness
goto result
:python
python -B -u -m validation.v10800_release_readiness
:result
set "RC=%errorlevel%"
if not "%RC%"=="0" echo V108: blokada wdrozenia; nie zatrzymano serwera.
exit /b %RC%
