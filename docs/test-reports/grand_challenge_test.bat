@echo off
echo ============================================
echo GRAND CHALLENGE TEST SUITE (3 Final Cases)
echo ============================================
echo.

echo Test 1: Multi-Heteroatom Fused Biaryl + Prime Locants
echo Name: 6,6'-dibromo-2,2'-biquinoline
echo 6,6'-dibromo-2,2'-biquinoline | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo Test 2: Fused Heterocycle + Indicated Hydrogen + Suffix + Halogen
echo Name: 5-chloro-1-methyl-1H-indole-2-carboxylic acid
echo 5-chloro-1-methyl-1h-indole-2-carboxylic acid | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo Test 3: Charged Heterocycle + SMILES Export
echo Name: 1-methylpyridin-1-ium chloride
echo 1-methylpyridin-1-ium chloride | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo ============================================
echo GRAND CHALLENGE TEST COMPLETE
echo ============================================
pause