@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
  py -3 -B -u "%~dp0audyt_v107_windows_przed_predeploy.py"
  goto done
)
python -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
  python -B -u "%~dp0audyt_v107_windows_przed_predeploy.py"
  goto done
)
echo BLAD: Wymagany Python 3.12 lub nowszy.
set "AUDYT_STATUS=2"
goto finish
:done
set "AUDYT_STATUS=%errorlevel%"
:finish
echo.
echo Wynik audytu v107: %AUDYT_STATUS% (0 = kod przeszedl, 3 = blokady wdrozenia).
echo Jezeli blokady istnieja, NIE uruchamiaj wdrozenia.
pause
exit /b %AUDYT_STATUS%
