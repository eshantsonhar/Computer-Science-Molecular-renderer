@echo off
echo Starting Molecular Parser Server...
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Node.js not found
    echo Please install Node.js from: https://nodejs.org/
    pause
    exit /b 1
)

REM Check if parser is compiled
if not exist "bin\aldehyde_parser.exe" (
    echo Parser not found. Running setup...
    call setup_cpp_environment.bat
    if %ERRORLEVEL% NEQ 0 (
        echo Setup failed
        pause
        exit /b 1
    )
)

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install express cors
)

REM Start the server
echo.
echo Starting server on http://localhost:3000
echo.
node parser_server.js