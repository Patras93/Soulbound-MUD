@echo off
setlocal
cd /d "%~dp0..\..\"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
set "SOULBOUND_V106_STAGING="
echo TESTY Soulbound v106 na osobnych kopiach. NIE WDRAZAC.
py -3 -B -m validation.v10600_kompletny_audyt_jedna_paczka %*
if errorlevel 1 (
  echo FAIL. WERSJA NIEZATWIERDZONA.
  exit /b 1
)
echo LOKALNE TESTY PASS. NADAL WYMAGANY WINDOWS PREDEPLOY.
exit /b 0
