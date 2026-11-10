const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

const page = readFileSync(
    path.join(__dirname, "..", "atomview_main.html"),
    "utf8"
);

function readRendererMap(name) {
    const mapMatch = page.match(
        new RegExp(`const ${name} = \\{([\\s\\S]*?)\\n        \\};`)
    );
    assert.ok(mapMatch, `Expected ${name} in the main renderer.`);
    return Object.fromEntries(
        [...mapMatch[1].matchAll(/'([^']+)':\s*(0x[0-9A-Fa-f]+|[0-9.]+)/g)]
            .map(([, element, value]) => [
                element,
                value.startsWith("0x") ? Number.parseInt(value, 16) : Number(value)
            ])
    );
}

const colors = readRendererMap("atomColors");
const sizes = readRendererMap("atomSizes");
const atomicNumbers = readRendererMap("elementAtomicNumbers");

for (const element of ["B", "Si", "P", "Se", "As", "Ge", "Sn", "Te"]) {
    assert.ok(colors[element], `Expected a distinct ${element} atom color.`);
    assert.ok(sizes[element] > 0, `Expected an explicit ${element} atom radius.`);
    assert.ok(atomicNumbers[element] > 0, `Expected ${element} atomic-number metadata.`);
}

assert.equal(colors.P, 0xFF8000, "Phosphorus should use the CPK orange color.");
assert.match(page, /function drawComputedGeometry\(result\)[\s\S]*?result\.atoms\.forEach/);
assert.match(page, /function drawComputedGeometry\(result\)[\s\S]*?result\.bonds\.forEach/);
assert.match(page, /atomData\.atomicNumber/);
assert.match(page, /atom\.userData\.atomicNumber = atomicNumber \|\| elementAtomicNumbers\[element\]/);
assert.match(page, /const molecularGraph = jsonData\.graph/);
assert.match(page, /renderComputedGeometry\(\{ graph: molecularGraph \}\)/);
assert.match(page, /Graph JSON uses atom and bond arrays/);

console.log("Main renderer element palette and geometry checks passed.");
