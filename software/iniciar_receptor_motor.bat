@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    call instalar.bat
    if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -m neiron.server --profile motor-pump --input external --open-browser %*
if errorlevel 1 (
    echo No se pudo abrir el banco. Revise el mensaje anterior.
    pause
)
