@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUNBUFFERED=1"

rem Uruchamiaj z folderu, w ktorym jest ten plik .bat (takze przez NVDA).
cd /d "%~dp0" 2>nul
if errorlevel 1 (
    echo BLAD: Nie mozna otworzyc folderu Soulbound: "%~dp0"
    echo Nie mozna zapisac logu w niedostepnym folderze.
    pause
    exit /b 10
)

rem Przygotuj logi ZANIM sprawdzimy Pythona i pliki serwera.
set "SOULBOUND_LOG_DIR=%CD%\logs"
if not exist "%SOULBOUND_LOG_DIR%\" mkdir "%SOULBOUND_LOG_DIR%" 2>nul
if not exist "%SOULBOUND_LOG_DIR%\" (
    set "SOULBOUND_LOG_DIR=%TEMP%\Soulbound-MUD-logs"
    if not exist "%SOULBOUND_LOG_DIR%\" mkdir "%SOULBOUND_LOG_DIR%" 2>nul
)
if not exist "%SOULBOUND_LOG_DIR%\" (
    echo BLAD: Nie mozna utworzyc folderu logow ani w grze, ani w TEMP.
    echo Sprawdz uprawnienia dysku i ilosc wolnego miejsca.
    pause
    exit /b 11
)
set "START_LOG=%SOULBOUND_LOG_DIR%\start.log"
set "ERROR_LOG=%SOULBOUND_LOG_DIR%\bledy.log"
>> "%START_LOG%" echo [%date% %time%] START launchera Soulbound
if errorlevel 1 (
    echo BLAD: Nie mozna zapisac logu startowego: "%START_LOG%"
    echo Sprawdz uprawnienia i wolne miejsce.
    pause
    exit /b 12
)
echo Logi startu: "%START_LOG%"
echo Logi bledow: "%ERROR_LOG%"

if not exist "start_windows_bootstrap.py" (
    call :fatal "Brakuje start_windows_bootstrap.py. Rozpakuj cala paczke Soulbound." 23
    goto :finish
)
if not exist "host_windows.py" (
    call :fatal "Brakuje host_windows.py. Rozpakuj cala paczke Soulbound." 20
    goto :finish
)
if not exist "server.py" (
    call :fatal "Brakuje server.py. Rozpakuj cala paczke Soulbound." 21
    goto :finish
)

rem Preferuj Python Launcher, a jezeli go nie ma - python z PATH.
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
    goto :start_server
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    goto :start_server
)
call :fatal "Nie znaleziono dzialajacego Pythona 3.12 lub nowszego. Sprawdz polecenia py -3 i python." 22
goto :finish

:start_server
>> "%START_LOG%" echo [%date% %time%] Start: %PY_CMD% -u start_windows_bootstrap.py
%PY_CMD% -u start_windows_bootstrap.py
set "result=%errorlevel%"
>> "%START_LOG%" echo [%date% %time%] Koniec procesu. Kod: %result%
if not "%result%"=="0" (
    >> "%ERROR_LOG%" echo [%date% %time%] BLAD: Serwer zakonczyl sie kodem %result%. Szczegoly: serwer.log oraz bledy.log.
    echo Serwer zakonczyl sie bledem. Zobacz logs\bledy.log i logs\serwer.log.
)
goto :finish

:fatal
set "reason=%~1"
set "result=%~2"
echo BLAD: %reason%
>> "%START_LOG%" echo [%date% %time%] BLAD: %reason%
>> "%ERROR_LOG%" echo [%date% %time%] BLAD STARTU: %reason%
exit /b 0

:finish
if not "%result%"=="0" pause
exit /b %result%
