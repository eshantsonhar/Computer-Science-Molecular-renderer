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
const elementCrystalModels = JSON.parse(
    readFileSync(path.join(root, "element_crystal_models.json"), "utf8")
);
const cobaltPage = readFileSync(path.join(root, "pages", "element_27.html"), "utf8");
const generator = readFileSync(path.join(root, "generate_element_pages.js"), "utf8");
assert.match(periodicTable, /Validated molecular and crystal models/);
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
assert.match(template, /buildCubicCrystal\(crystalStructure, displayedFormula\)/);
assert.match(template, /window\.AtomViewCrystalRenderer\.buildCubicCrystal/);
assert.match(template, /No validated molecular or crystal geometry is available/);
assert.doesNotMatch(template, /This example represents a solid, ionic, coordination/);

const crystalTypes = new Set(["rocksalt", "cesium-chloride", "zincblende", "fluorite", "fractional-cell"]);
const crystalElements = Object.entries(elementData).filter(([, element]) => element.crystal_structure);
assert.ok(crystalElements.length >= 20, "Crystal model coverage should extend beyond the cobalt example.");
const atomColors = template.slice(template.indexOf("const atomColors"), template.indexOf("const atomSizes"));
const hasColorFallback =
    /function getAtomColor\(element\)/.test(template) &&
    /new THREE\.Color\(\)\.setHSL\(hue, 0\.68, 0\.62\)/.test(template);
assert.ok(hasColorFallback, "Unlisted elements should receive deterministic, distinct colors.");
for (const [atomicNumber, element] of crystalElements) {
    const structure = element.crystal_structure;
    assert.ok(crystalTypes.has(structure.type), `${element.name} uses a supported crystal prototype.`);
    const modelElements = structure.type === "fractional-cell"
        ? structure.basis.map(site => site.element)
        : [structure.cation, structure.anion];
    if (structure.type === "fractional-cell") {
        assert.ok(structure.source_cod_id, `${element.name} crystal data should identify its COD source.`);
        assert.ok(structure.space_group);
        assert.ok(structure.basis.length > 0);
        assert.ok(Object.values(structure.lattice_parameters_angstrom).every(value =>
            Number.isFinite(value) && value > 0
        ));
        assert.ok(structure.basis.every(site =>
            typeof site.element === "string" &&
            Array.isArray(site.fractional) &&
            site.fractional.length === 3 &&
            site.fractional.every(Number.isFinite)
        ));
    } else {
        assert.ok(Number.isFinite(structure.lattice_constant_angstrom) && structure.lattice_constant_angstrom > 0);
        assert.ok(structure.cation && structure.anion && structure.cation !== structure.anion);
    }
    assert.ok(modelElements.every(symbol => atomColors.includes(`'${symbol}'`) || hasColorFallback));
    const page = readFileSync(path.join(root, "pages", `element_${atomicNumber}.html`), "utf8");
    assert.ok(
        page.includes(`const crystalStructure = ${JSON.stringify(structure)}`),
        `${element.name}'s generated page should include its crystal data.`
    );
    assert.match(page, /<script src="\.\.\/crystal-renderer\.js"><\/script>/);
    assert.match(page, /buildCubicCrystal\(crystalStructure, displayedFormula\)/);
}

const discreteMoleculeFormulas = new Set(["H₂O", "H₃BO₃", "CO₂", "NH₃", "HF", "H₃PO₄", "H₂SO₄"]);
for (const [atomicNumber, element] of Object.entries(elementData)) {
    if (element.is_unstable || element.category === "noble-gas") continue;
    assert.ok(
        element.crystal_structure ||
            elementCrystalModels[atomicNumber] ||
            discreteMoleculeFormulas.has(element.molecule_formula),
        `${element.name} should have a molecular or solid-state display model.`
    );
    if (elementCrystalModels[atomicNumber]) {
        assert.equal(elementCrystalModels[atomicNumber].element, element.symbol);
        const page = readFileSync(path.join(root, "pages", `element_${atomicNumber}.html`), "utf8");
        assert.ok(
            page.includes(`const elementalCrystalStructure = ${JSON.stringify(elementCrystalModels[atomicNumber])}`),
            `${element.name}'s generated page should include its elemental crystal model.`
        );
        assert.match(page, /buildElementalCrystal\(elementalCrystalStructure\)/);
    }
}

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
