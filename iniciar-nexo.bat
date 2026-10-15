@echo off
REM NEXO: arranca Python + PHP en modo conectado (MySQL). Doble clic y listo.
cd /d "%~dp0"
echo Iniciando NEXO...
taskkill /FI "WINDOWTITLE eq NEXO Python*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq NEXO PHP*" /F >nul 2>&1
start "NEXO Python" ".venv\Scripts\python.exe" backend\app.py --port 8001
start "NEXO PHP" php -S 127.0.0.1:8000 server/router.php
timeout /t 4 /nobreak >nul
start http://127.0.0.1:8000
echo Listo. Para detener, cierra las ventanas NEXO Python y NEXO PHP.
pause
