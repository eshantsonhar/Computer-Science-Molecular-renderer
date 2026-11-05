const { createHash } = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { createWriteStream } = require('node:fs');
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');

const projectRoot = path.resolve(__dirname, '..');
const publicDirectory = path.join(projectRoot, 'public');
const opsinDirectory = path.join(projectRoot, 'api', 'vendor', 'opsin');
const jarPath = path.join(opsinDirectory, 'opsin-core-2.9.0.jar');
const bridgePath = path.join(opsinDirectory, 'bridge', 'OpsinBridge.class');
const jarSha256 = '627ee5da4af551f9c4d1d766f545eb7cf519a344776e0bb677247a47abac0252';
const jreSha256 = 'a535a1df9c6284d9618872984e026ae0352d1f7e9e0605425c0e6114f47351dd';
const jreUrl = 'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz';
const publicExtensions = new Set([
    '.css', '.gif', '.html', '.ico', '.jpeg', '.jpg', '.js', '.json',
    '.otf', '.png', '.svg', '.ttf', '.wasm', '.webp', '.woff', '.woff2'
]);
const excludedRootFiles = new Set([
    'generate_element_pages.js',
    'package-lock.json',
    'package.json',
    'parser_server.js',
    'vercel.json'
]);

function sha256(filePath) {
    return createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function copyPublicFiles(sourceDirectory, destinationDirectory) {
    for (const entry of fs.readdirSync(sourceDirectory, { withFileTypes: true })) {
        const sourcePath = path.join(sourceDirectory, entry.name);
        const destinationPath = path.join(destinationDirectory, entry.name);
        if (entry.isDirectory()) {
            fs.mkdirSync(destinationPath, { recursive: true });
            copyPublicFiles(sourcePath, destinationPath);
        } else if (entry.isFile() && publicExtensions.has(path.extname(entry.name).toLowerCase())) {
            fs.copyFileSync(sourcePath, destinationPath);
        }
    }
}

function prepareStaticOutput() {
    fs.rmSync(publicDirectory, { recursive: true, force: true });
    fs.mkdirSync(publicDirectory, { recursive: true });

    for (const entry of fs.readdirSync(projectRoot, { withFileTypes: true })) {
        if (entry.isFile() && !excludedRootFiles.has(entry.name)) {
            const extension = path.extname(entry.name).toLowerCase();
            if (publicExtensions.has(extension)) {
                fs.copyFileSync(
                    path.join(projectRoot, entry.name),
                    path.join(publicDirectory, entry.name)
                );
            }
        } else if (entry.isDirectory() && ['assets', 'pages'].includes(entry.name)) {
            const destination = path.join(publicDirectory, entry.name);
            fs.mkdirSync(destination, { recursive: true });
            copyPublicFiles(path.join(projectRoot, entry.name), destination);
        }
    }

    if (!fs.existsSync(path.join(publicDirectory, 'atomview_main.html'))) {
        throw new Error('The static build did not include atomview_main.html.');
    }
    if (fs.existsSync(path.join(publicDirectory, 'api'))) {
        throw new Error('API implementation files must not be copied to the public directory.');
    }
}

async function installLinuxRuntime() {
    const runtimeDirectory = path.join(opsinDirectory, 'runtime');
    const javaPath = path.join(runtimeDirectory, 'bin', 'java');
    if (fs.existsSync(javaPath)) return;

    const archivePath = path.join(os.tmpdir(), `atomview-temurin-${process.pid}.tar.gz`);
    try {
        const response = await fetch(jreUrl);
        if (!response.ok || !response.body) {
            throw new Error(`JRE download failed with HTTP ${response.status}.`);
        }
        await pipeline(Readable.fromWeb(response.body), createWriteStream(archivePath));
        if (sha256(archivePath) !== jreSha256) {
            throw new Error('Downloaded JRE checksum did not match the pinned release.');
        }

        fs.mkdirSync(runtimeDirectory, { recursive: true });
        execFileSync('tar', ['-xzf', archivePath, '-C', runtimeDirectory, '--strip-components=1'], {
            stdio: 'inherit'
        });
        if (!fs.existsSync(javaPath)) {
            throw new Error('The extracted JRE does not contain its Java executable.');
        }
    } finally {
        fs.rmSync(archivePath, { force: true });
    }
}

async function main() {
    prepareStaticOutput();

    if (!fs.existsSync(jarPath) || sha256(jarPath) !== jarSha256) {
        throw new Error('The vendored OPSIN core JAR is missing or failed its SHA-256 check.');
    }
    if (!fs.existsSync(bridgePath)) {
        throw new Error('The compiled local OPSIN bridge is missing.');
    }

    if (process.platform === 'linux') {
        await installLinuxRuntime();
    } else {
        console.log('The pinned Linux JRE is provisioned only for Vercel; local development uses Java on PATH.');
    }
}

main().catch(error => {
    console.error(`Preparing the local IUPAC parser failed: ${error.message}`);
    process.exitCode = 1;
});
