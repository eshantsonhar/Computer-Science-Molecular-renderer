@echo off
echo Auto-Restarting Molecular Parser Server...
echo Press Ctrl+C to stop completely
echo.

:restart
echo [%date% %time%] Starting server...
node parser_server.js

echo [%date% %time%] Server stopped. Restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto restart