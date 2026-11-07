@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
py -3 -u "%~dp0predeploy_v108_z_zewnatrz.py" %*
if errorlevel 9009 python -u "%~dp0predeploy_v108_z_zewnatrz.py" %*
set "WYNIK=%errorlevel%"
echo.
echo V108 PREDEPLOY: %WYNIK%. 0 = PASS. Pozostale = NIE WDRAZAC.
pause
exit /b %WYNIK%
