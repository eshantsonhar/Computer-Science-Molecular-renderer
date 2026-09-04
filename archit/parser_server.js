const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// Parse molecule endpoint
app.post('/parse', (req, res) => {
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

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'Server running', parser: fs.existsSync('bin/aldehyde_parser.exe') });
});

app.listen(PORT, () => {
    console.log(`Parser server running on http://localhost:${PORT}`);
    console.log('C++ parser integration ready!');
});