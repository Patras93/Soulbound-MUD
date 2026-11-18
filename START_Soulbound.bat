@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "PYTHONDONTWRITEBYTECODE=1"
rem Visible, standard BAT entrypoint; the Python host detaches without hidden script host.
call "%~dp0Start-Soulbound-Windows.bat"
exit /b !errorlevel!
