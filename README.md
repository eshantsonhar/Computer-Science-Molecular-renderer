# AtomView - Molecular Renderer

An interactive 3D molecular visualization tool for organic chemistry, featuring straight-chain and aromatic molecule rendering with an interactive molecule drawing interface.

## Features

- **Straight Chain Molecules**: Parse and render alkanes, alkenes, alkynes, alcohols, aldehydes, ketones, halogens, and epoxides
- **Aromatic Molecules**: Full support for benzene derivatives, heterocycles, and complex fused systems
- **Interactive Molecule Editor**: Draw skeletal structures and convert them to 3D renderings
- **Client-Side Parsing**: JavaScript parsers for both straight-chain and aromatic molecules (no server required)
- **Server Fallback**: Optional C++ parsers for advanced functionality

## Deployment

### Netlify Deployment

This project is configured for direct deployment to Netlify:

1. **Drag and Drop**: Simply drag the `atom_view_final` folder to Netlify's drop deployment
2. **Git Integration**: Connect to GitHub repository and deploy from there
3. **Configuration**: The `netlify.toml` file handles routing and build settings

### Local Development

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Start Server** (optional, for C++ parser fallback):
   ```bash
   node parser_server.js
   ```

3. **Open in Browser**:
   - The application will work entirely client-side without the server
   - Access at `http://localhost:3000` if running the server

## File Structure

- `molecular_renderer_integrated.html` - Main application interface
- `straight_chain_parser.js` - JavaScript parser for straight-chain molecules
- `aromatic_parser.js` - JavaScript parser for aromatic molecules
- `lol.html` - Interactive molecule drawing interface
- `parser_server.js` - Optional Node.js server for C++ parser fallback
- `netlify.toml` - Netlify deployment configuration
- `index.html` - Entry point with redirect

## Usage

1. **Straight Chain Molecules**: Enter IUPAC names like "ethan-1-ol", "2-methylpropane", etc.
2. **Aromatic Molecules**: Enter names like "benzene", "1-chlorobenzene", "1,3,5-trinitrobenzene"
3. **Molecule Editor**: Click "Molecule Editor" in the sidebar to draw custom structures
4. **JSON Input**: Directly input JSON data for rendering

## Credits

Developed by Eshant, Soham, Arush, Archit