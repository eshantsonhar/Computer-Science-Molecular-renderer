@echo off
title Molecular Renderer - Easy Start
color 0A

echo.
echo  ███╗   ███╗ ██████╗ ██╗     ███████╗ ██████╗██╗   ██╗██╗      █████╗ ██████╗ 
echo  ████╗ ████║██╔═══██╗██║     ██╔════╝██╔════╝██║   ██║██║     ██╔══██╗██╔══██╗
echo  ██╔████╔██║██║   ██║██║     █████╗  ██║     ██║   ██║██║     ███████║██████╔╝
echo  ██║╚██╔╝██║██║   ██║██║     ██╔══╝  ██║     ██║   ██║██║     ██╔══██║██╔══██╗
echo  ██║ ╚═╝ ██║╚██████╔╝███████╗███████╗╚██████╗╚██████╔╝███████╗██║  ██║██║  ██║
echo  ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝
echo.
echo                           🧪 MOLECULAR RENDERER 🧪
echo                              Easy Start Launcher
echo.
echo ================================================================================

REM Check if we're in the right directory
if not exist "molecular_renderer.html" (
    echo ❌ Error: Please run this from your project folder
    echo    Looking for: molecular_renderer.html
    echo    Current folder: %CD%
    pause
    exit /b 1
)

echo ✅ Project folder found: %CD%
echo.

REM Check if server is already running
echo 🔍 Checking if server is already running...
curl -s http://localhost:3000/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Server is already running!
    goto :open_browser
)

echo 🚀 Starting molecular parser server...
echo.

REM Check Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js not found
    echo 📥 Please install Node.js from: https://nodejs.org/
    echo    Then run this script again.
    pause
    exit /b 1
)
echo ✅ Node.js found

REM Check parser
if not exist "bin\aldehyde_parser.exe" (
    echo 🔧 C++ parser not found. Compiling...
    call setup_cpp_environment.bat
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Setup failed
        pause
        exit /b 1
    )
)
echo ✅ C++ parser ready

REM Install dependencies
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install express cors --silent
)
echo ✅ Dependencies ready

REM Start server in background
echo 🌐 Starting server...
start /min "Molecular Parser Server" cmd /c "title Molecular Parser Server && echo Server starting... && node parser_server.js"

REM Wait for server with progress
echo 🕐 Waiting for server to initialize...
set /a counter=0
:wait_loop
set /a counter+=1
echo    Attempt %counter%...
timeout /t 1 /nobreak >nul
curl -s http://localhost:3000/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if %counter% LSS 10 goto wait_loop
    echo ❌ Server failed to start after 10 seconds
    echo 🔧 Try running: node parser_server.js
    pause
    exit /b 1
)

echo ✅ Server started successfully!

:open_browser
echo 🌐 Opening molecular renderer...
echo.
echo ================================================================================
echo  🎉 SUCCESS! Your molecular renderer is ready!
echo ================================================================================
echo.
echo  🔗 Server: http://localhost:3000
echo  🧪 Renderer: Opening in your default browser...
echo.
echo  💡 Tips:
echo     • Keep this window open (server runs here)
echo     • Try molecules like: ethanol, 2-methylpropane, butan-2-one
echo     • Close this window to stop the server
echo.
echo ================================================================================

REM Open the HTML file
start "" "molecular_renderer.html"

echo.
echo 🖥️  Molecular renderer opened in browser
echo 🔄 Server is running... (Press Ctrl+C to stop)
echo.

REM Keep server running
node parser_server.js