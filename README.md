HEAD
# Molecular Structure Parser & Renderer

A complete system that uses your C++ parser to generate molecular structures and renders them in 3D using Three.js.

##  Quick Start

### Step 1: Set Up C++ Environment
```cmd
setup_cpp_environment.bat
```
This will:
- Check for C++ compiler (installs MinGW if needed)
- Compile your `aldehyde.cpp` parser
- Test the parser with sample molecules

### Step 2: Start the Server
```cmd
start_server.bat
```
This will:
- Install Node.js dependencies
- Start the parser server on http://localhost:3000
- Enable communication between HTML and C++ parser

### Step 3: Open the Renderer
Open `molecular_renderer.html` in your browser

##  Project Structure

```
├── aldehyde.cpp              # Your original C++ parser (enhanced)
├── molecular_renderer.html   # 3D molecular renderer
├── parser_server.js          # Node.js server for C++ integration
├── setup_cpp_environment.bat # Automated C++ setup
├── start_server.bat          # Server startup script
├── run_parser.bat            # Direct parser testing
└── bin/
    └── aldehyde_parser.exe   # Compiled parser (generated)
```

##  How It Works

1. **Input**: Enter IUPAC molecule name in HTML interface
2. **Parse**: HTML sends request to Node.js server
3. **Execute**: Server runs your compiled C++ parser
4. **Output**: Parser generates JSON structure
5. **Render**: HTML receives JSON and renders 3D molecule

##  Supported Molecules

Your C++ parser handles:
- **Alkanes**: methane, ethane, propane, etc.
- **Alkenes**: ethene, propene, butene, etc.
- **Alkynes**: ethyne, propyne, etc.
- **Alcohols**: methanol, ethanol, propanol, etc.
- **Aldehydes**: methanal, ethanal, etc.
- **Ketones**: propanone, butanone, etc.
- **Halogens**: fluoro, chloro, bromo, iodo compounds
- **Complex**: 2-methylpropan-1-ol, 3-chlorobutane, etc.

##  Example Usage

### Via HTML Interface:
1. Open `molecular_renderer.html`
2. Enter: `2-methylpropan-1-ol`
3. Click "Parse & Render"
4. View 3D structure

### Via Command Line:
```cmd
run_parser.bat
# Enter: ethanol
# Output: JSON structure + 3D coordinates
```

### Direct C++ Usage:
```cmd
echo ethanol | bin\aldehyde_parser.exe
type output.json
```

## Troubleshooting

### "No C++ compiler found"
- Run: `setup_cpp_environment.bat`
- Or install manually: https://www.mingw-w64.org/

### "Server offline"
- Run: `start_server.bat`
- Check if Node.js is installed: https://nodejs.org/

### "Parser execution failed"
- Ensure `bin\aldehyde_parser.exe` exists
- Re-run: `setup_cpp_environment.bat`

## Features

### C++ Parser (Your Original Logic)
-  Maintains your exact parsing algorithm
-  Same class structure and functions
-  Generates identical JSON output
-  No changes to core logic

### 3D Renderer
-  Interactive 3D visualization
-  CPK coloring scheme
-  Proper bond types (single, double, triple)
-  Realistic atom sizes
-  Mouse controls (rotate, zoom, pan)

### Integration
-  Real-time parsing via HTTP API
-  Automatic JSON transfer
-  Error handling and validation
-  Server status monitoring

Development Workflow

1. **Modify Parser**: Edit `aldehyde.cpp`
2. **Recompile**: Run `setup_cpp_environment.bat`
3. **Test**: Use `run_parser.bat` for quick testing
4. **Visualize**: Refresh HTML page to see changes

Output Format

Your C++ parser generates JSON like:
```json
[
  {"locantnumber":"0","numberofatoms":"2"},
  {"locantnumber":"2","group":"alcohol"}
]
```

The renderer converts this to 3D coordinates and renders:
- Carbon atoms as gray spheres
- Oxygen atoms as red spheres  
- Hydrogen atoms as white spheres
- Bonds as cylinders (single/double/triple)

 Controls

- **Mouse**: Rotate view
- **Scroll**: Zoom in/out
- **Examples**: Click preset molecules
- **JSON**: Paste direct parser output

Your C++ parser logic remains completely intact while gaining a powerful 3D visualization interface!

# Computer-Science-Molecular-renderer
A molecular renderer that parses and renders all organic molecules
 45ae00c22262e6109f015b34e80032ddb735922a
