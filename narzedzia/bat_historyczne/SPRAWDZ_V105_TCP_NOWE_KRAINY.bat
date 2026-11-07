@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0..\..\"
cd /d "%ROOT%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
echo SOULBOUND V105: izolowany test TCP 5 graczy w nowych krainach.
echo TYLKO localhost i baza TEMP; nie dotyka produkcji.
py -3 -u -m validation.v10500_tcp_endgame_regions
if errorlevel 1 (
  echo BLAD: test nowych krain TCP nie przeszedl.
  pause
  exit /b 1
)
echo PASS: test TCP nowych krain.
pause
exit /b 0
