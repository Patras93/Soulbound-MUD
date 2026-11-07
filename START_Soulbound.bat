@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem Visible, standard BAT entrypoint; the Python host detaches without hidden script host.
call "%~dp0Start-Soulbound-Windows.bat"
exit /b !errorlevel!
