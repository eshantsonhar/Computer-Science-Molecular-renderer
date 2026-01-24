@echo off
echo Starting Molecular Parser Server in background...
echo.
echo Server will run until you close this window or restart your computer.
echo To stop the server, close this window or press Ctrl+C.
echo.
echo Server Status: http://localhost:3000/health
echo HTML Renderer: Open molecular_renderer.html in your browser
echo.
echo ========================================
echo Server is running... (Keep this window open)
echo ========================================
echo.

node parser_server.js

echo.
echo Server stopped.
pause