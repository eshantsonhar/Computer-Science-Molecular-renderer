@echo off
echo Molecular Parser - Enter molecule names to parse
echo Type 'exit' to quit
echo ========================================
echo.

:loop
set /p molecule="Enter molecule name: "
if /i "%molecule%"=="exit" goto :end
if "%molecule%"=="" goto :loop

echo %molecule% | bin\aldehyde_parser.exe

if exist "output.json" (
    echo.
    echo ✓ Parsed successfully! JSON saved to output.json
    echo Content:
    type output.json
    echo.
    echo ----------------------------------------
) else (
    echo ✗ Parsing failed
)

goto :loop

:end
echo Goodbye!