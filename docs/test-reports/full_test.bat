@echo off
echo Full aromatic parser test suite (12 molecules)
echo ===============================================
echo.

echo Test 1: 1,3-thiazole
echo 1,3-thiazole | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 2: 5-methyl-1,3,4-thiadiazole-2-thiol
echo 5-methyl-1,3,4-thiadiazole-2-thiol | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 3: 2,4,6-trichlorophenol
echo 2,4,6-trichlorophenol | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 4: 4,5-dichloro-1,3-dioxolan-2-one
echo 4,5-dichloro-1,3-dioxolan-2-one | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 5: benzo[b]thiophene
echo benzo[b]thiophene | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 6: furo[2,3-c]pyridine
echo furo[2,3-c]pyridine | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 7: thieno[3,2-b]furan
echo thieno[3,2-b]furan | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 8: 1H-pyrrolo[2,3-b]pyridine
echo 1H-pyrrolo[2,3-b]pyridine | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 9: 4-(difluoromethyl)-2-nitrobenzoic acid
echo 4-(difluoromethyl)-2-nitrobenzoic acid | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 10: 5-(4-chlorophenyl)-1,3-oxazole
echo 5-(4-chlorophenyl)-1,3-oxazole | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 11: 2-amino-5-bromo-1,3-benzoxazole-7-carboxylic acid
echo 2-amino-5-bromo-1,3-benzoxazole-7-carboxylic acid | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Test 12: 3,5-dimethyl-4-nitro-1H-pyrazole
echo 3,5-dimethyl-4-nitro-1H-pyrazole | bin\aromatic_parser.exe
type aromatic_output.json
echo.
echo.

echo Full test suite complete!
pause