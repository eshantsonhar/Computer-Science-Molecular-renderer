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
const vendorDirectory = path.join(projectRoot, 'api', 'vendor');
const opsinDirectory = path.join(vendorDirectory, 'opsin');
const linuxDrawingLibraryDirectory = path.join(vendorDirectory, 'rdkit_runtime_libs');
const orthonymJarDirectory = path.join(vendorDirectory, 'orthonym_jars');
const jarPath = path.join(opsinDirectory, 'opsin-core-2.9.0.jar');
const bridgePath = path.join(opsinDirectory, 'bridge', 'OpsinBridge.class');
const runtimeDirectory = path.join(opsinDirectory, 'runtime');
const runtimeArchivePath = path.join(opsinDirectory, 'runtime-linux-x64.tar.gz');
const jarSha256 = '627ee5da4af551f9c4d1d766f545eb7cf519a344776e0bb677247a47abac0252';
const jdkSha256 = 'd7f5d5cf865a2902b70ff549b97586a7d3f234e016f041ab447ea740c7d66d1c';
const jdkUrl = 'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/OpenJDK21U-jdk_x64_linux_hotspot_21.0.13_9.tar.gz';
const orthonymJars = [
    {
        filename: 'opsin-cli-2.9.0-jar-with-dependencies.jar',
        url: 'https://github.com/dan2097/opsin/releases/download/2.9.0/opsin-cli-2.9.0-jar-with-dependencies.jar',
        sha256: 'c2e29326c281f87b59a05d934d8589adac6e9d17b95b984931b3e739111b360f'
    },
    {
        filename: 'centres-cli-1.2.1.jar',
        url: 'https://github.com/SiMolecule/centres/releases/download/1.2.1/centres.jar',
        sha256: '6c5d5cafa9393ed7b667a2340222348cd15a9bbdd0d1b92518229f26cc5e87fb'
    }
];
const linuxDrawingPackages = [
    {
        filename: 'libxrender1_0.9.10-1_amd64.deb',
        url: 'https://deb.debian.org/debian/pool/main/libx/libxrender/libxrender1_0.9.10-1_amd64.deb',
        sha256: '3ea17d07b5aa89012130e2acd92f0fc0ea67314e2f5eab6e33930ef688f48294'
    },
    {
        filename: 'libx11-6_1.7.2-1+deb11u2_amd64.deb',
        url: 'https://deb.debian.org/debian/pool/main/libx/libx11/libx11-6_1.7.2-1%2Bdeb11u2_amd64.deb',
        sha256: '2b3b959cb10c07be065eb638a8577fe20f282045aaef76425dbd7310d1244b8c'
    },
    {
        filename: 'libxext6_1.3.3-1.1_amd64.deb',
        url: 'https://deb.debian.org/debian/pool/main/libx/libxext/libxext6_1.3.3-1.1_amd64.deb',
        sha256: 'dc1ff8a2b60c7dd3c8917ffb9aa65ee6cda52648d9150608683c47319d1c0c8c'
    },
    {
        filename: 'libxcb1_1.14-3_amd64.deb',
        url: 'https://deb.debian.org/debian/pool/main/libx/libxcb/libxcb1_1.14-3_amd64.deb',
        sha256: 'd5e0f047ed766f45eb7473947b70f9e8fddbe45ef22ecfd92ab712c0671a93ac'
    },
    {
        filename: 'libxau6_1.0.9-1_amd64.deb',
        url: 'https://deb.debian.org/debian/pool/main/libx/libxau/libxau6_1.0.9-1_amd64.deb',
        sha256: '679db1c4579ec7c61079adeaae8528adeb2e4bf5465baa6c56233b995d714750'
    },
    {
        filename: 'libxdmcp6_1.1.2-3_amd64.deb',
        url: 'https://deb.debian.org/debian/pool/main/libx/libxdmcp/libxdmcp6_1.1.2-3_amd64.deb',
        sha256: 'ecb8536f5fb34543b55bb9dc5f5b14c9dbb4150a7bddb3f2287b7cab6e9d25ef'
    },
    {
        filename: 'libbsd0_0.11.3-1+deb11u1_amd64.deb',
        url: 'https://deb.debian.org/debian/pool/main/libb/libbsd/libbsd0_0.11.3-1%2Bdeb11u1_amd64.deb',
        sha256: '6ec5a08a4bb32c0dc316617f4bbefa8654c472d1cd4412ab8995f3955491f4a8'
    },
    {
        filename: 'libmd0_1.0.3-3_amd64.deb',
        url: 'https://deb.debian.org/debian/pool/main/libm/libmd/libmd0_1.0.3-3_amd64.deb',
        sha256: '9e425b3c128b69126d95e61998e1b5ef74e862dd1fc953d91eebcc315aea62ea'
    }
];
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

async function downloadAndVerify(url, destination, expectedSha256, description) {
    const response = await fetch(url);
    if (!response.ok || !response.body) {
        throw new Error(`${description} download failed with HTTP ${response.status}.`);
    }
    await pipeline(Readable.fromWeb(response.body), createWriteStream(destination));
    if (await sha256(destination) !== expectedSha256) {
        throw new Error(`${description} checksum did not match the pinned release.`);
    }
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
        await downloadAndVerify(jdkUrl, archivePath, jdkSha256, 'JDK');

        fs.rmSync(temporaryDirectory, { recursive: true, force: true });
        fs.mkdirSync(temporaryDirectory, { recursive: true });
        execFileSync('tar', ['-xzf', archivePath, '-C', temporaryDirectory, '--strip-components=1'], {
            stdio: 'inherit'
        });
        fs.rmSync(runtimeDirectory, { recursive: true, force: true });
        fs.rmSync(runtimeDirectory, { recursive: true, force: true });
        execFileSync(
            path.join(temporaryDirectory, 'bin', 'jlink'),
            [
                '--module-path',
                path.join(temporaryDirectory, 'jmods'),
                '--add-modules',
                'java.base,java.xml,java.desktop',
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

async function installOrthonymJars() {
    fs.mkdirSync(orthonymJarDirectory, { recursive: true });
    for (const jar of orthonymJars) {
        await downloadAndVerify(
            jar.url,
            path.join(orthonymJarDirectory, jar.filename),
            jar.sha256,
            jar.filename
        );
    }
    console.log('Verified and staged the pinned offline Orthonym naming resources.');
}

async function installLinuxDrawingLibraries() {
    const temporaryDirectory = path.join(os.tmpdir(), `atomview-x11-${process.pid}`);
    fs.rmSync(temporaryDirectory, { recursive: true, force: true });
    fs.mkdirSync(temporaryDirectory, { recursive: true });

    try {
        const packagePaths = [];
        for (const packageInfo of linuxDrawingPackages) {
            const packagePath = path.join(temporaryDirectory, packageInfo.filename);
            await downloadAndVerify(
                packageInfo.url,
                packagePath,
                packageInfo.sha256,
                packageInfo.filename
            );
            packagePaths.push(packagePath);
        }

        fs.rmSync(linuxDrawingLibraryDirectory, { recursive: true, force: true });
        execFileSync(
            'python3',
            [
                path.join(projectRoot, 'scripts', 'extract-debian-runtime-libraries.py'),
                linuxDrawingLibraryDirectory,
                ...packagePaths
            ],
            { stdio: 'inherit' }
        );
        console.log('Verified and staged the pinned Linux libraries required by RDKit SVG rendering.');
    } finally {
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
    await installOrthonymJars();

    if (process.platform === 'linux') {
        await installLinuxRuntime();
        await installLinuxDrawingLibraries();
    } else {
        fs.rmSync(runtimeArchivePath, { force: true });
        console.log('The pinned minimal Linux Java runtime is provisioned only for Vercel; local development uses Java on PATH. Vercel installs the pinned Python dependencies from requirements.txt.');
    }
}

main().catch(error => {
    console.error(`Preparing the local IUPAC parser failed: ${error.message}`);
    process.exitCode = 1;
});
