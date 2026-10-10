@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
echo SOULBOUND - TEST POLACZEN TCP
 echo Uruchom Soulbound przed testem. Test nie loguje sie na postacie.
py -3.12 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3.12 -u "%~dp0validation\v2003_tcp_stress.py"
    goto finish
)
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3 -u "%~dp0validation\v2003_tcp_stress.py"
    goto finish
)
python -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    python -u "%~dp0validation\v2003_tcp_stress.py"
    goto finish
)
echo BLAD: wymaga Python 3.12 lub nowszy.
set "RESULT=2"
goto pause
:finish
set "RESULT=%ERRORLEVEL%"
:pause
echo.
echo LOG DO PRZESLANIA: "%~dp0logs\TESTY_TCP_Soulbound.log"
pause
exit /b %RESULT%
