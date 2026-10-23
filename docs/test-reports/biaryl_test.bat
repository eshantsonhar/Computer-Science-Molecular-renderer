@echo off
echo ============================================
echo BIARYL ASSEMBLY STRESS TEST SUITE (3 Cases)
echo ============================================
echo.

echo Test 1: Symmetric Symmetrical Biaryl
echo Name: 1,1'-biphenyl
echo 1,1'-biphenyl | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo Test 2: Multi-Heteroatom Biaryl with Prime Locants
echo Name: 2,2'-bipyridine
echo 2,2'-bipyridine | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo Test 3: Substituted Biheterocycle with Prime Locants
echo Name: 5,5'-dibromo-2,2'-bithiophene
echo 5,5'-dibromo-2,2'-bithiophene | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo ============================================
echo BIARYL ASSEMBLY TEST COMPLETE
echo ============================================
pause