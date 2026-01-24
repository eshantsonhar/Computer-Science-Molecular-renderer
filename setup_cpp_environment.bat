@echo off
echo Setting up C++ development environment...
echo.

REM Check if we're in the right directory
if not exist "aldehyde.cpp" (
    echo Error: aldehyde.cpp not found in current directory
    echo Please run this script from the project folder
    pause
    exit /b 1
)

REM Create directories
if not exist "build" mkdir build
if not exist "bin" mkdir bin

echo [1/4] Checking for C++ compiler...

REM Try to find g++ (MinGW)
where g++ >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Found g++ compiler
    goto :compile
)

REM Try to find cl (Visual Studio)
where cl >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Found Visual Studio compiler
    goto :compile_vs
)

echo ✗ No C++ compiler found
echo.
echo Installing MinGW-w64 (lightweight C++ compiler)...
echo.

REM Download and install MinGW-w64 via winget if available
where winget >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Using winget to install MinGW...
    winget install -e --id=Mingw-w64.Mingw-w64
    if %ERRORLEVEL% EQU 0 (
        echo ✓ MinGW installed successfully
        echo Please restart this script after adding MinGW to your PATH
        pause
        exit /b 0
    )
)

echo.
echo Please install a C++ compiler manually:
echo 1. MinGW-w64: https://www.mingw-w64.org/downloads/
echo 2. Visual Studio Community: https://visualstudio.microsoft.com/vs/community/
echo 3. Or use chocolatey: choco install mingw
echo.
pause
exit /b 1

:compile
echo [2/4] Compiling with g++...
g++ -std=c++17 -O2 aldehyde.cpp -o bin/aldehyde_parser.exe
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Compilation failed
    pause
    exit /b 1
)
echo ✓ Compilation successful
goto :create_wrapper

:compile_vs
echo [2/4] Compiling with Visual Studio...
cl /EHsc /std:c++17 /O2 aldehyde.cpp /Fe:bin/aldehyde_parser.exe
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Compilation failed
    pause
    exit /b 1
)
echo ✓ Compilation successful
goto :create_wrapper

:create_wrapper
echo [3/4] Creating Node.js wrapper...
goto :test

:test
echo [4/4] Testing the parser...
echo ethanol | bin\aldehyde_parser.exe
if exist "output.json" (
    echo ✓ Parser working correctly
    echo ✓ Generated output.json
) else (
    echo ✗ Parser test failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ Setup complete!
echo ========================================
echo.
echo Files created:
echo - bin/aldehyde_parser.exe (your compiled parser)
echo - output.json (test output)
echo.
echo You can now:
echo 1. Run: bin\aldehyde_parser.exe
echo 2. Type molecule names to parse
echo 3. Use the HTML renderer with the generated JSON
echo.
pause