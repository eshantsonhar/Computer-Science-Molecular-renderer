const express = require('express');
const { execFile } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const cors = require('cors');

const app = express();
const ROOT_DIR = __dirname;
const PORT = Number.parseInt(process.env.PORT || '3000', 10);
const HOST = process.env.HOST || '0.0.0.0';
const PARSER_PATH = process.env.PARSER_PATH || path.join(ROOT_DIR, 'bin', process.platform === 'win32' ? 'aldehyde_parser.exe' : 'aldehyde_parser');
const MAX_MOLECULE_LENGTH = 200;
const PARSER_TIMEOUT_MS = Number.parseInt(process.env.PARSER_TIMEOUT_MS || '15000', 10);

app.disable('x-powered-by');
app.use(cors());
app.use(express.json({ limit: '8kb' }));
app.use(express.static(ROOT_DIR, { extensions: ['html'] }));

function parserAvailable() {
    return fs.existsSync(PARSER_PATH);
}

function runParser(moleculeName) {
    return new Promise((resolve, reject) => {
        const workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'molecular-parser-'));
        const outputPath = path.join(workDir, 'output.json');
        const child = execFile(PARSER_PATH, { cwd: workDir, timeout: PARSER_TIMEOUT_MS, windowsHide: true }, (error, stdout, stderr) => {
            try {
                if (error) return reject(error);
                if (!fs.existsSync(outputPath)) return reject(new Error('No output file generated'));
                resolve(JSON.parse(fs.readFileSync(outputPath, 'utf8')));
            } catch (parseError) {
                reject(parseError);
            } finally {
                fs.rmSync(workDir, { recursive: true, force: true });
            }
        });
        child.stdin.end(`${moleculeName}\n`);
    });
}

app.post('/parse', async (req, res) => {
    const { moleculeName } = req.body || {};
    if (typeof moleculeName !== 'string' || !moleculeName.trim()) {
        return res.status(400).json({ error: 'Molecule name is required' });
    }
    const normalizedName = moleculeName.trim();
    if (normalizedName.length > MAX_MOLECULE_LENGTH || /[\u0000-\u001f\u007f]/.test(normalizedName)) {
        return res.status(400).json({ error: `Molecule name must be between 1 and ${MAX_MOLECULE_LENGTH} safe characters` });
    }
    if (!parserAvailable()) {
        return res.status(503).json({ error: 'Parser executable is not available on this server' });
    }
    try {
        const data = await runParser(normalizedName);
        return res.json({ success: true, data, molecule: normalizedName });
    } catch (error) {
        console.error('Parser request failed:', error.message);
        return res.status(500).json({ error: 'Parser execution failed' });
    }
});

app.get('/health', (req, res) => {
    const available = parserAvailable();
    res.status(available ? 200 : 503).json({
        status: 'Server running',
        parser: available,
        parserPath: path.relative(ROOT_DIR, PARSER_PATH),
    });
});

app.use((error, req, res, next) => {
    if (error instanceof SyntaxError && error.status === 400) {
        return res.status(400).json({ error: 'Invalid JSON request body' });
    }
    console.error('Unhandled server error:', error);
    return res.status(500).json({ error: 'Internal server error' });
});

const server = app.listen(PORT, HOST, () => {
    console.log(`Parser server listening on ${HOST}:${PORT}`);
    console.log(`Parser executable: ${PARSER_PATH}`);
});

function shutdown(signal) {
    console.log(`${signal} received, shutting down`);
    server.close(() => process.exit(0));
}
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

module.exports = app;
