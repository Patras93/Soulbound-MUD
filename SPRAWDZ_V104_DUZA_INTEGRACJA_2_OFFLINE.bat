@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo BLAD: Brak launcher Python py. Uruchom: python -m validation.v10400_suite_safe
  exit /b 2
)
py -3 -m validation.v10400_suite_safe
if errorlevel 1 (
  echo FAIL - nie wdrazaj tej paczki.
  exit /b 1
)
echo PASS TESTY OFFLINE. Windows PREDEPLOY i TCP nadal sa obowiazkowe.
exit /b 0
