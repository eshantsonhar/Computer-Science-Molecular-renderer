@echo off
REM 1. Compile the C++ file
REM This assumes g++ (MinGW) is installed and in your PATH
g++ aldehyde.cpp -o aldehyde_parser.exe

REM 2. Create the bin directory if it doesn't exist
if not exist "bin" mkdir bin

REM 3. Move the executable to the bin folder
move aldehyde_parser.exe .\bin\
