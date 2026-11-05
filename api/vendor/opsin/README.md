# Vendored OPSIN

This directory contains OPSIN 2.9.0, used locally to translate supported chemical names to SMILES before RDKit generates coordinates.

- Upstream: https://github.com/dan2097/opsin/tree/2.9.0
- Source revision: `b91b610af5ab07560fedb20730d7aef46bb2bca0`
- License: MIT; see [`LICENSE.txt`](./LICENSE.txt).
- `src/main/java` and `src/main/resources` are the corresponding upstream core source and parsing data.
- `opsin-core-2.9.0.jar` is the upstream release artifact, SHA-256 `627ee5da4af551f9c4d1d766f545eb7cf519a344776e0bb677247a47abac0252`.
- `java/OpsinBridge.java` is the small local stdin/stdout adapter; `bridge/OpsinBridge.class` is compiled for Java 8 bytecode compatibility.

To rebuild the bridge with a JDK:

```text
javac -source 8 -target 8 -encoding UTF-8 -classpath opsin-core-2.9.0.jar -d bridge java/OpsinBridge.java
```

On Linux, `npm run build` downloads the pinned Eclipse Temurin 21 JDK, verifies its SHA-256, and uses `jlink` to create a runtime containing only the `java.base` and `java.xml` modules. It smoke-tests the bridge, compresses the runtime into the ignored `runtime-linux-x64.tar.gz` archive, and removes the expanded runtime and temporary JDK. Vercel packages this archive, this JAR, and the compiled bridge with the Python function; the Python API extracts the runtime to `/tmp` on first IUPAC-name use. It does not bundle the OPSIN source tree or full JDK. Local development may instead use Java 21 on `PATH`. No OPSIN-hosted API is called.
