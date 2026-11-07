@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0..\..\"
set "SB_LIVE=C:\Soulbound-MUD"
if not "%~1"=="" set "SB_ZIP=%~f1"
if defined SB_ZIP (
  python -u "%~dp0..\..\wdroz_v107_z_zewnatrz.py" --instalacja "%SB_LIVE%" --zip "%SB_ZIP%"
) else (
  python -u "%~dp0..\..\wdroz_v107_z_zewnatrz.py" --instalacja "%SB_LIVE%"
)
set "SB_EXIT=%ERRORLEVEL%"
echo.
echo WYNIK POMOSTU V107: %SB_EXIT%
if not "%SB_EXIT%"=="0" echo NIE WDROZONO. SPRAWDZ KOMUNIKAT POWYZEJ.
pause
exit /b %SB_EXIT%
