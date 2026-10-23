@echo off
echo ============================================
echo STRESS TEST SUITE (4 Complex Molecules)
echo ============================================
echo.

echo Test 1: High Substituent Density (Collision Check)
echo Name: 1,3,5-tribromo-2,4,6-trinitrobenzene
echo 1,3,5-tribromo-2,4,6-trinitrobenzene | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo Test 2: Fused Heterocycle + Multiplicative Locants + Indicated Hydrogen
echo Name: 5,6-difluoro-1H-benzo[d]imidazole-2-carboxylic acid
echo 5,6-difluoro-1h-benzo[d]imidazole-2-carboxylic acid | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo Test 3: Polycyclic Aromatic Hydrocarbon (PAH)
echo Name: 1,4-dichloronaphthalene
echo 1,4-dichloronaphthalene | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo Test 4: Multi-Heteroatom Fused System
echo Name: 2,7-dichloro-1,8-naphthyridine
echo 2,7-dichloro-1,8-naphthyridine | bin\aromatic_parser.exe
echo Parsed JSON:
type aromatic_output.json
echo.
echo.

echo ============================================
echo STRESS TEST COMPLETE
echo ============================================
pause