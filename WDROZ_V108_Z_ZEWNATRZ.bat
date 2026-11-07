@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3 -u "%~dp0wdroz_v108_z_zewnatrz.py" %*
if errorlevel 9009 python -u "%~dp0wdroz_v108_z_zewnatrz.py" %*
set "WYNIK=%errorlevel%"
echo.
echo Wynik bramki v108: %WYNIK%. 0 = PASS/wykonano, inne = odmowa.
pause
exit /b %WYNIK%
