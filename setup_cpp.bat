@echo off
REM 1. Compile the C++ files
REM This assumes g++ (MinGW) is installed and in your PATH
g++ aldehyde.cpp -o aldehyde_parser.exe
g++ aromatic_parser.cpp -o aromatic_parser.exe

REM 2. Create the bin directory if it doesn't exist
if not exist "bin" mkdir bin

REM 3. Move the executables to the bin folder
move aldehyde_parser.exe .\bin\
move aromatic_parser.exe .\bin\
