@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Start BAT only creates a detached Python host. The BAT/CMD exits immediately.
if exist "%TEMP%\" cd /d "%TEMP%" >nul 2>&1
if exist "%SystemRoot%\System32\wscript.exe" (
    "%SystemRoot%\System32\wscript.exe" //nologo "%~dp0START_Soulbound_UKRYTY.vbs"
    if not errorlevel 1 exit /b 0
)
call "%~dp0Start-Soulbound-Windows.bat"
exit /b %errorlevel%
