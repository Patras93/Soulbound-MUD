@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
cd /d "%ROOT%"
if errorlevel 1 (
  echo BLAD: Nie mozna otworzyc folderu Soulbound.
  pause
  exit /b 2
)
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUNBUFFERED=1"
set "PYTHONDONTWRITEBYTECODE=1"
echo.
echo SOULBOUND: TESTY TAKIE JAK NA RAILWAY
echo Wynik zostanie zapisany w logs\TESTY_Soulbound.log
echo Aby przerwac testy, nacisnij Ctrl+C.
echo.
py -3.12 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3.12 -u "%ROOT%testuj_soulbound_windows.py"
    goto finished
)
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3 -u "%ROOT%testuj_soulbound_windows.py"
    goto finished
)
python -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    python -u "%ROOT%testuj_soulbound_windows.py"
    goto finished
)
if not exist "%ROOT%logs" mkdir "%ROOT%logs" >nul 2>&1
>"%ROOT%logs\TESTY_Soulbound.log" echo BLAD: Nie znaleziono Pythona 3.12 lub nowszego. Zainstaluj Python 3.12 i uruchom TESTUJ_Soulbound.bat ponownie.
echo BLAD: Wymagany Python 3.12 lub nowszy. Szczegoly w logs\TESTY_Soulbound.log.
set "RESULT=2"
goto finish_pause
:finished
set "RESULT=%ERRORLEVEL%"
:finish_pause
echo.
echo LOG DO PRZESLANIA: "%ROOT%logs\TESTY_Soulbound.log"
echo.
pause
exit /b %RESULT%
