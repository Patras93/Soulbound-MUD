@echo off
setlocal
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%CD%"
echo Soulbound v104 - zbiorcza kontrola przedwdrozeniowa OFFLINE
python -m validation.v10400_release_gate
if errorlevel 1 goto blad
echo.
echo Kontrola offline PASS. Do wdrozenia wymagane testy Windows/TCP i migracja BigNumber.
pause
exit /b 0
:blad
echo.
echo KONTROLA FAIL. NIE WDRAZAC.
pause
exit /b 1
