@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONIOENCODING=utf-8"
set "SOULBOUND_DB="
set "DATABASE_URL="
set "SOULBOUND_PORT="
set "SOULBOUND_HOST="
set "PORT="
set "REPORT_DIR=%USERPROFILE%\Downloads"
if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"
set "REPORT=%REPORT_DIR%\SOULBOUND_V104_KONTROLA_WINDOWS_PL.txt"
set "MIGRATION_REPORT=%REPORT_DIR%\SOULBOUND_V104_MIGRACJA_KOPIA_PL.txt"
set "PY=py -3"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if errorlevel 1 (
    set "PY=python"
    python -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo BLAD: wymagany Python 3.12 lub nowszy.
        exit /b 2
    )
)
echo SOULBOUND v104: audyt Windows w TEMP, bez instalacji i wdrozenia.
echo Uwaga: testy historyczne moga trwac dlugo.
%PY% -u -m validation.v10400_one_archive_verify --pelny --raport "%REPORT%"
set "RESULT=%ERRORLEVEL%"
echo.
echo Raport testow Windows: "%REPORT%"
set "SOURCE_DB=%~1"
if "%SOURCE_DB%"=="" set "SOURCE_DB=C:\Soulbound-MUD\soulbound.db"
if exist "%SOURCE_DB%" (
    echo.
    echo Proba BigNumber na tymczasowej kopii; zrodlo SQLite tylko do odczytu.
    %PY% -u -m validation.v10400_migration_rehearsal --db "%SOURCE_DB%" > "%MIGRATION_REPORT%" 2>&1
    if errorlevel 1 set "RESULT=1"
    echo Raport migracji: "%MIGRATION_REPORT%"
) else (
    echo.
    echo POMINIETO probna migracje: brak pliku "%SOURCE_DB%".
    set "RESULT=1"
)
echo.
if not "%RESULT%"=="0" (
    echo NIEZALICZONE lub NIEPELNE: nie wdrazaj Soulbound v104.
) else (
    echo Kontrole diagnostyczne PASS. To nadal NIE JEST zgoda na wdrozenie.
    echo Nadal wymagany oficjalny Windows PREDEPLOY 60/60 oraz pelne produkcyjne BigNumber.
)
echo Dzialajacy serwer i prawdziwa baza nie zostaly podmienione przez ten skrypt.
endlocal & exit /b %RESULT%
