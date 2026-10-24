@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
echo SOULBOUND - PRAWDZIWA WALKA W ODDZIELNEJ KOPII SERWERA.
echo Ta gra testowa uzywa portu 4900 i NIE zmienia bazy na porcie 4000.
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -u "%~dp0arena_real_izolowana.py" --source "%~dp0" --port 4900
) else (
  python -u "%~dp0arena_real_izolowana.py" --source "%~dp0" --port 4900
)
exit /b %errorlevel%
