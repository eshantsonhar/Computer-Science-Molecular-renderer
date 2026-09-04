@echo off
echo ============================================
echo ADVANCED FRONTIER STRESS TEST SUITE (3 Cases)
echo ============================================
echo.

echo Test 1: Substituted Aromatic Group as a Substituent
echo Name: 4-(4-bromophenyl)-1,3-thiazole
echo 4-(4-bromophenyl)-1,3-thiazole | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo Test 2: Aromatic Cation / Salt Handling
echo Name: 1-methylpyridin-1-ium chloride
echo 1-methylpyridin-1-ium chloride | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo Test 3: Multi-heteroatom Fused Locant Alignment
echo Name: 2-amino-4-methylquinoline
echo 2-amino-4-methylquinoline | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo ============================================
echo ADVANCED FRONTIER TEST COMPLETE
echo ============================================
pause