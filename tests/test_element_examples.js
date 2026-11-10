const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const template = readFileSync(path.join(root, "pages", "element_template.html"), "utf8");

for (const [atomicNumber, formula] of [[15, "H₃PO₄"], [16, "H₂SO₄"]]) {
    const page = readFileSync(
        path.join(root, "pages", `element_${atomicNumber}.html`),
        "utf8"
    );
    assert.ok(
        template.includes(`'${formula}'`),
        `${formula} should be included in the supported discrete molecules.`
    );
    assert.match(page, /requestMolecularGeometry\(\{/);
    assert.match(page, /bondOrders/);
}

assert.match(template, /atom\.bondOrders\?\.\[bondIndex\]/);
assert.match(template, /neighbor\.bondOrders\?\.\[index\]/);

console.log("Periodic-table molecule examples use explicit, neighbor-specific bond orders.");
