@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
echo SOULBOUND: 6 GRACZY TCP - OSOBNY SERWER 127.0.0.1 I BAZA TYMCZASOWA.
echo Ten test nie korzysta z bazy prawdziwych postaci.
py -3.12 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3.12 -u "validation\v2102_tcp_six_players.py"
    goto finished
)
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3 -u "validation\v2102_tcp_six_players.py"
    goto finished
)
python -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
    python -u "validation\v2102_tcp_six_players.py"
    goto finished
)
echo BLAD: Brak Pythona 3.12 lub nowszego.
set "RESULT=2"
goto finish_pause
:finished
set "RESULT=%ERRORLEVEL%"
:finish_pause
echo WYNIK TESTU TCP: %RESULT% (0 oznacza PASS)
pause
exit /b %RESULT%
