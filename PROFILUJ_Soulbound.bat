@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Start the usual detached server with optional performance summaries enabled.
rem Stop a running copy via STOP_Soulbound.bat before starting profiling.
set "SOULBOUND_PERF_LOG=1"
call "%~dp0Start-Soulbound-Windows.bat"
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (
  echo Pomiar Soulbound wlaczony. Normalny serwer w tle.
  echo Walcz z 10-20 mobami i przeslij logs\serwer.log.
  echo Szukaj w logu wierszy: SOULBOUND PERF.
  echo Wroc do zwyklego START_Soulbound.bat aby wylaczyc pomiar.
  echo Najpierw uzyj STOP_Soulbound.bat przed ponownym startem.
) else (
  echo Nie udalo sie uruchomic pomiaru. Sprawdz logs\start.log.
)
echo.
pause
exit /b %RESULT%
