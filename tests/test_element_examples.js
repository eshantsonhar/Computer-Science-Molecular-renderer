const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const template = readFileSync(path.join(root, "pages", "element_template.html"), "utf8");
const periodicTable = readFileSync(
    path.join(root, "pages", "periodic_table.html"),
    "utf8"
);
const elementData = JSON.parse(readFileSync(path.join(root, "elements_data.json"), "utf8"));
const cobaltPage = readFileSync(path.join(root, "pages", "element_27.html"), "utf8");
const generator = readFileSync(path.join(root, "generate_element_pages.js"), "utf8");
assert.match(periodicTable, /validated isolated-molecule geometry/);
assert.deepEqual(elementData["27"].crystal_structure, {
    type: "rocksalt",
    cation: "Co",
    anion: "O",
    lattice_constant_angstrom: 4.26
});
assert.match(generator, /CRYSTAL_STRUCTURE/g);
assert.match(cobaltPage, /const crystalStructure = \{"type":"rocksalt","cation":"Co","anion":"O","lattice_constant_angstrom":4\.26\}/);
assert.match(cobaltPage, /function buildRocksaltCrystal\(structure\)/);
assert.match(cobaltPage, /Lines show nearest-neighbor coordination, not covalent molecular bonds/);

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
