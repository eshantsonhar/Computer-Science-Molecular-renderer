@echo off
REM 1. Install C++ compiler and Unzip
winget install -e --id GNU.GCC
winget install -e --id Microsoft.PowerShell

REM 2. Install Node.js (Current Version)
winget install -e --id OpenJS.NodeJS.Current

REM 3. Refresh the path for the current session so 'npm' works
set "PATH=%PATH%;%ProgramFiles%\nodejs\"

REM 4. Install Node packages
call npm install express cors

REM 5. Run setup and server scripts
call setup_cpp.bat
call start_server.bat

pause
