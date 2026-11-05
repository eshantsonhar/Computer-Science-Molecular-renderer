const { createHash } = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { createReadStream, createWriteStream } = require('node:fs');
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');

const projectRoot = path.resolve(__dirname, '..');
const publicDirectory = path.join(projectRoot, 'public');
const opsinDirectory = path.join(projectRoot, 'api', 'vendor', 'opsin');
const jarPath = path.join(opsinDirectory, 'opsin-core-2.9.0.jar');
const bridgePath = path.join(opsinDirectory, 'bridge', 'OpsinBridge.class');
const runtimeDirectory = path.join(opsinDirectory, 'runtime');
const runtimeArchivePath = path.join(opsinDirectory, 'runtime-linux-x64.tar.gz');
const jarSha256 = '627ee5da4af551f9c4d1d766f545eb7cf519a344776e0bb677247a47abac0252';
const jdkSha256 = 'd7f5d5cf865a2902b70ff549b97586a7d3f234e016f041ab447ea740c7d66d1c';
const jdkUrl = 'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/OpenJDK21U-jdk_x64_linux_hotspot_21.0.13_9.tar.gz';
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

async function sha256(filePath) {
    const hash = createHash('sha256');
    for await (const chunk of createReadStream(filePath)) {
        hash.update(chunk);
    }
    return hash.digest('hex');
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
    const javaPath = path.join(runtimeDirectory, 'bin', 'java');

    const temporaryDirectory = path.join(os.tmpdir(), `atomview-temurin-jdk-${process.pid}`);
    const archivePath = path.join(os.tmpdir(), `atomview-temurin-jdk-${process.pid}.tar.gz`);
    try {
        const response = await fetch(jdkUrl);
        if (!response.ok || !response.body) {
            throw new Error(`JDK download failed with HTTP ${response.status}.`);
        }
        await pipeline(Readable.fromWeb(response.body), createWriteStream(archivePath));
        if (await sha256(archivePath) !== jdkSha256) {
            throw new Error('Downloaded JDK checksum did not match the pinned release.');
        }

        fs.rmSync(temporaryDirectory, { recursive: true, force: true });
        fs.mkdirSync(temporaryDirectory, { recursive: true });
        execFileSync('tar', ['-xzf', archivePath, '-C', temporaryDirectory, '--strip-components=1'], {
            stdio: 'inherit'
        });

        fs.rmSync(runtimeDirectory, { recursive: true, force: true });
        fs.mkdirSync(runtimeDirectory, { recursive: true });
        execFileSync(
            path.join(temporaryDirectory, 'bin', 'jlink'),
            [
                '--module-path',
                path.join(temporaryDirectory, 'jmods'),
                '--add-modules',
                'java.base,java.xml',
                '--strip-debug',
                '--no-header-files',
                '--no-man-pages',
                '--compress=2',
                '--output',
                runtimeDirectory
            ],
            {
                stdio: 'inherit'
            }
        );
        if (!fs.existsSync(javaPath)) {
            throw new Error('The linked Java runtime does not contain its Java executable.');
        }

        const classPath = [
            path.join(opsinDirectory, 'bridge'),
            jarPath
        ].join(path.delimiter);
        const bridgeOutput = execFileSync(
            javaPath,
            ['-cp', classPath, 'OpsinBridge'],
            {
                encoding: 'utf8',
                input: 'ethanol\n'
            }
        );
        if (!bridgeOutput.startsWith('SUCCESS\t')) {
            throw new Error('The linked Java runtime failed the local OPSIN smoke test.');
        }

        fs.rmSync(runtimeArchivePath, { force: true });
        execFileSync(
            'tar',
            ['-czf', runtimeArchivePath, '-C', opsinDirectory, 'runtime'],
            { stdio: 'inherit' }
        );
        const archiveSize = fs.statSync(runtimeArchivePath).size;
        if (archiveSize === 0) {
            throw new Error('The compressed Java runtime archive is empty.');
        }
        fs.rmSync(runtimeDirectory, { recursive: true, force: true });
        console.log(`Created minimal Java runtime archive (${(archiveSize / 1024 / 1024).toFixed(1)} MB).`);
    } finally {
        fs.rmSync(archivePath, { force: true });
        fs.rmSync(temporaryDirectory, { recursive: true, force: true });
    }
}

async function main() {
    prepareStaticOutput();

    if (!fs.existsSync(jarPath) || await sha256(jarPath) !== jarSha256) {
        throw new Error('The vendored OPSIN core JAR is missing or failed its SHA-256 check.');
    }
    if (!fs.existsSync(bridgePath)) {
        throw new Error('The compiled local OPSIN bridge is missing.');
    }

    if (process.platform === 'linux') {
        await installLinuxRuntime();
    } else {
        fs.rmSync(runtimeArchivePath, { force: true });
        console.log('The pinned minimal Linux Java runtime is provisioned only for Vercel; local development uses Java on PATH.');
    }
}

main().catch(error => {
    console.error(`Preparing the local IUPAC parser failed: ${error.message}`);
    process.exitCode = 1;
});
