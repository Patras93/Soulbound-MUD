@echo off
setlocal EnableExtensions DisableDelayedExpansion
if exist "%TEMP%\" cd /d "%TEMP%" >nul 2>&1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
echo Soulbound - automatyczna aktualizacja z ZIP (kopia bazy i kodu).
if not exist "%~dp0aktualizuj_soulbound.py" (
  echo BLAD: Brakuje aktualizuj_soulbound.py. Rozpakuj kompletna paczke.
  pause
  exit /b 2
)
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
  py -3 -u "%~dp0aktualizuj_soulbound.py" %*
  goto :koniec
)
python -c "import sys;sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 (
  python -u "%~dp0aktualizuj_soulbound.py" %*
  goto :koniec
)
echo BLAD: Wymagany Python 3.12 lub nowszy.
set "WYNIK=2"
goto :pauza
:koniec
set "WYNIK=%errorlevel%"
:pauza
echo.
echo Nacisnij dowolny klawisz, aby zamknac aktualizator.
pause >nul
exit /b %WYNIK%
