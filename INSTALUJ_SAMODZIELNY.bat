@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONDONTWRITEBYTECODE=1"
set "TARGET=%~dp0..\Soulbound-Samodzielny"
if not "%~1"=="" set "TARGET=%~f1"
python -m systems.current_install install --target "%TARGET%"
if errorlevel 1 (
  echo Instalacja przerwana. Istniejacego katalogu ani danych nie nadpisano.
  exit /b 1
)
echo Gotowe. Nowa gra: "%TARGET%"
