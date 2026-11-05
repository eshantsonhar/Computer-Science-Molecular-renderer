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

`npm run build` provisions the pinned Eclipse Temurin 21 Linux JRE into the ignored `runtime/` directory and verifies its SHA-256 before extraction. Vercel packages that runtime with this JAR and bridge. Local development may instead use Java 21 on `PATH`. No OPSIN-hosted API is called.
