@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto verify
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -m venv .venv
    if not errorlevel 1 goto verify
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; assert sys.version_info[:2] == (3,12)" >nul 2>nul
    if not errorlevel 1 (
        python -m venv .venv
        if not errorlevel 1 goto verify
    )
)
set "NEIRON_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%NEIRON_PY%" (
    "%NEIRON_PY%" -m venv .venv
    if not errorlevel 1 goto verify
)
echo No se encontro Python 3.12. Instale Python 3.12 para su usuario y vuelva a ejecutar.
echo No se han instalado paquetes ni cambiado la configuracion del sistema.
pause
exit /b 1
:verify
.venv\Scripts\python.exe -c "import sys,sqlite3; assert sys.version_info[:2] == (3,12); print('Entorno aislado listo. Python',sys.version.split()[0],'- SQLite',sqlite3.sqlite_version)"
if errorlevel 1 (
    echo El entorno existente requiere revision: se necesita Python 3.12.
    pause
    exit /b 1
)
echo No se requieren paquetes ni internet. Abra iniciar.bat.
exit /b 0
