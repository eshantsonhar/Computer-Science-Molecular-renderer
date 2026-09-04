const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

// Import JS parsers
const StraightChainParser = require('./straight_chain_parser');
const AromaticParser = require('./aromatic_parser');

const app = express();
// Use environment variable for port, default to 3000
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// Parse molecule endpoint (JS parser)
app.post('/parse', (req, res) => {
    const { moleculeName } = req.body;
    
    if (!moleculeName) {
        return res.status(400).json({ error: 'Molecule name is required' });
    }

    try {
        const parser = new StraightChainParser();
        const result = parser.parse(moleculeName);
        res.json({ success: true, data: result, molecule: moleculeName });
    } catch (error) {
        console.error('JS Parser error:', error);
        res.status(500).json({ error: 'JS Parser execution failed: ' + error.message });
    }
});

// Parse molecule endpoint (C++ fallback)
app.post('/parse-cpp', (req, res) => {
    const { moleculeName } = req.body;
    
    if (!moleculeName) {
        return res.status(400).json({ error: 'Molecule name is required' });
    }

    // Run the C++ parser (using your original file-based approach)
    const command = `echo ${moleculeName} | bin\\aldehyde_parser.exe`;
    
    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error('Parser error:', error);
            return res.status(500).json({ error: 'Parser execution failed: ' + error.message });
        }

        // Read the generated JSON file
        try {
            if (fs.existsSync('output.json')) {
                const jsonData = fs.readFileSync('output.json', 'utf8');
                const parsedData = JSON.parse(jsonData);
                res.json({ success: true, data: parsedData, molecule: moleculeName });
            } else {
                res.status(500).json({ error: 'No output file generated' });
            }
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            res.status(500).json({ error: 'Invalid JSON output: ' + parseError.message });
        }
    });
});

// Parse aromatic molecule endpoint (JS parser)
app.post('/parse-aromatic', (req, res) => {
    const { moleculeName } = req.body;
    
    if (!moleculeName) {
        return res.status(400).json({ error: 'Molecule name is required' });
    }

    console.log('Received molecule:', moleculeName);

    try {
        const parser = new AromaticParser();
        const result = parser.parse(moleculeName);
        res.json({ success: true, data: result, molecule: moleculeName });
    } catch (error) {
        console.error('JS Aromatic parser error:', error);
        res.status(500).json({ error: 'JS Aromatic parser execution failed: ' + error.message });
    }
});

// Parse aromatic molecule endpoint (C++ fallback)
app.post('/parse-aromatic-cpp', (req, res) => {
    const { moleculeName } = req.body;
    
    if (!moleculeName) {
        return res.status(400).json({ error: 'Molecule name is required' });
    }

    console.log('Received molecule:', moleculeName);

    // Write molecule name to a temp file, then pipe to parser
    const tempFile = 'temp_molecule.txt';
    fs.writeFileSync(tempFile, moleculeName);
    
    const command = `type ${tempFile} | bin\\aromatic_parser.exe`;
    
    console.log('Executing command:', command);
    
    exec(command, (error, stdout, stderr) => {
        // Clean up temp file
        try {
            if (fs.existsSync(tempFile)) {
                fs.unlinkSync(tempFile);
            }
        } catch (e) {
            console.error('Error cleaning temp file:', e);
        }

        if (error) {
            console.error('Aromatic parser error:', error);
            console.error('Stderr:', stderr);
            return res.status(500).json({ error: 'Aromatic parser execution failed: ' + error.message });
        }

        console.log('Parser stdout:', stdout);

        // Read the generated JSON file
        try {
            if (fs.existsSync('aromatic_output.json')) {
                const jsonData = fs.readFileSync('aromatic_output.json', 'utf8');
                const parsedData = JSON.parse(jsonData);
                res.json({ success: true, data: parsedData, molecule: moleculeName });
            } else {
                res.status(500).json({ error: 'No aromatic output file generated' });
            }
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            res.status(500).json({ error: 'Invalid JSON output: ' + parseError.message });
        }
    });
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'Server running', 
        jsParser: true,
        cppParser: fs.existsSync('bin/aldehyde_parser.exe'),
        jsAromaticParser: true,
        cppAromaticParser: fs.existsSync('bin/aromatic_parser.exe')
    });
});

// Force health check response for testing
app.get('/health-test', (req, res) => {
    res.json({ 
        status: 'Server running', 
        jsParser: true,
        cppParser: true,
        jsAromaticParser: true,
        cppAromaticParser: true
    });
});

app.listen(PORT, () => {
    console.log(`Parser server running on http://localhost:${PORT}`);
    console.log('C++ parser integration ready!');
    console.log('Health check available at http://localhost:3000/health');
});