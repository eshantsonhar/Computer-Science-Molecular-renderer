@echo off
echo Compiling C++ parser to WebAssembly...

REM Check if emscripten is installed
where emcc >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Emscripten not found. Please install Emscripten first.
    echo Visit: https://emscripten.org/docs/getting_started/downloads.html
    pause
    exit /b 1
)

REM Compile to WebAssembly
emcc aldehyde_wasm.cpp -o aldehyde_parser.js ^
    -s WASM=1 ^
    -s EXPORTED_FUNCTIONS="['_parse_molecule']" ^
    -s EXPORTED_RUNTIME_METHODS="['ccall','cwrap']" ^
    -s ALLOW_MEMORY_GROWTH=1 ^
    -s MODULARIZE=1 ^
    -s EXPORT_NAME="AldehydeModule" ^
    --bind

if %ERRORLEVEL% EQU 0 (
    echo Compilation successful!
    echo Generated files: aldehyde_parser.js and aldehyde_parser.wasm
) else (
    echo Compilation failed!
)

pause