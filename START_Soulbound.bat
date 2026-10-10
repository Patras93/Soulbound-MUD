@echo off
setlocal EnableExtensions
cd /d "%~dp0" || (echo BLAD: Brak folderu gry. & pause & exit /b 2)
if not exist "%~dp0START_Soulbound_UKRYTY.vbs" (
    echo BLAD: Brakuje START_Soulbound_UKRYTY.vbs.
    pause
    exit /b 2
)
if not exist "%~dp0Start-Soulbound-Windows.bat" (
    echo BLAD: Brakuje Start-Soulbound-Windows.bat.
    pause
    exit /b 2
)
if not exist "%SystemRoot%\System32\wscript.exe" goto :foreground
echo Soulbound: uruchamianie w tle. Logi: logs\serwer.log oraz logs\bledy.log.
"%SystemRoot%\System32\wscript.exe" //nologo "%~dp0START_Soulbound_UKRYTY.vbs"
if not errorlevel 1 exit /b 0
echo Nie udalo sie uruchomic w tle.
:foreground
echo Uruchamianie w trybie widocznym (Windows Script Host niedostepny).
call "%~dp0Start-Soulbound-Windows.bat"
exit /b %errorlevel%
