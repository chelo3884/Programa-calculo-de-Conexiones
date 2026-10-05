@echo off
rem Respaldo: abre el programa con una ventana de consola. Lo normal es usar Iniciar.pyw o el acceso directo.
cd /d "%~dp0"
where pythonw >nul 2>nul && (start "" pythonw Iniciar.pyw & exit /b)
where py >nul 2>nul && (start "" py -3w Iniciar.pyw & exit /b)
echo No se encontro Python. Instalelo desde https://www.python.org/downloads/ marcando "Add Python to PATH".
pause
