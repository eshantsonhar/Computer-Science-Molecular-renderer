@echo off
echo 🧪 Molecular Renderer Launcher
echo ================================
echo.

REM Check if server is already running
curl -s http://localhost:3000/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Server is already running!
    echo Opening renderer...
    start "" "molecular_renderer.html"
    exit /b 0
)

echo 🚀 Starting server and renderer...
echo.

REM Start server in background
start /min "Molecular Parser Server" cmd /c "echo Starting server... && node parser_server.js"

REM Wait for server to start
echo Waiting for server to initialize...
:wait_loop
timeout /t 1 /nobreak >nul
curl -s http://localhost:3000/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto wait_loop

echo ✅ Server started successfully!
echo 🌐 Opening molecular renderer...

REM Open the renderer
start "" "molecular_renderer.html"

echo.
echo ================================
echo ✅ Molecular Renderer is ready!
echo ================================
echo.
echo The server is running in the background.
echo You can close this window safely.
echo.
pause