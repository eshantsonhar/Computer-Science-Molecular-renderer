@echo off
echo Starting server on http://localhost:3000

REM Check if node is installed before running
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in your PATH.
    pause
    exit /b
)

node parser_server.js
