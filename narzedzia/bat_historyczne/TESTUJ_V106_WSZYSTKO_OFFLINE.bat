@echo off
setlocal
cd /d "%~dp0..\..\"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
set "SOULBOUND_V106_STAGING="
echo Soulbound v106: kompletny lokalny test, tylko osobna kopia. NIE WDRAZAC.
py -3 -B "validation\v10600_one_package_gate.py" %*
if errorlevel 1 (
  echo LOKALNY TEST V106 NIE PRZESZEDL. NIE WDRAZAC.
  exit /b 1
)
echo LOKALNE TESTY V106 ZAKONCZONE. TO NIE JEST PREDEPLOY.
exit /b 0
