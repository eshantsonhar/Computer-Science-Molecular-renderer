const { createHash } = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { createWriteStream } = require('node:fs');
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');

const opsinDirectory = path.resolve(__dirname, '..', 'api', 'vendor', 'opsin');
const jarPath = path.join(opsinDirectory, 'opsin-core-2.9.0.jar');
const bridgePath = path.join(opsinDirectory, 'bridge', 'OpsinBridge.class');
const jarSha256 = '627ee5da4af551f9c4d1d766f545eb7cf519a344776e0bb677247a47abac0252';
const jreSha256 = 'a535a1df9c6284d9618872984e026ae0352d1f7e9e0605425c0e6114f47351dd';
const jreUrl = 'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz';

function sha256(filePath) {
    return createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
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
