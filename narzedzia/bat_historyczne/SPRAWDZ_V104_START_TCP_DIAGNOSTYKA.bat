@echo off
setlocal
cd /d "%~dp0..\..\"
set "SOULBOUND_BOOT_TRACE=1"
set "PYTHONDONTWRITEBYTECODE=1"
echo SOULBOUND V104 - DIAGNOSTYKA STARTU TCP NA KOPII
 echo Test uruchamia TYLKO 127.0.0.1, losowy port i tymczasowa baze.
 echo NIE laczy sie z dzialajacym serwerem na porcie 4000.
python -c "from validation.v10400_tcp_loopback_smoke import run; print(run(startup_timeout=115))"
if errorlevel 1 (
  echo.
  echo NIE POTWIERDZONO GOTOWOSCI TCP. NIE WDRAZAC v104.
) else (
  echo.
  echo POWITANIE TCP POTWIERDZONE W TESTOWYM SERWERZE.
  echo Pełny PREDEPLOY nadal wymagany.
)
pause
endlocal
