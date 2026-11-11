const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const elementData = require(path.join(__dirname, "..", "elements_data.json"));

global.window = {};
require(path.join(__dirname, "..", "crystal-renderer.js"));

class Vector3 {
    constructor(x, y, z) {
        Object.assign(this, { x, y, z });
    }

    distanceToSquared(other) {
        return (this.x - other.x) ** 2 + (this.y - other.y) ** 2 + (this.z - other.z) ** 2;
    }
}

class Group {
    children = [];

    add(child) {
        this.children.push(child);
    }

    clear() {
        this.children = [];
    }
}

const THREE = {
    Vector3,
    BoxGeometry: class {
        constructor(...dimensions) {
            this.dimensions = dimensions;
        }
    },
    EdgesGeometry: class {
        constructor(geometry) {
            this.geometry = geometry;
        }
    },
    LineBasicMaterial: class {},
    BufferGeometry: class {
        setFromPoints(points) {
            this.points = points;
            return this;
        }
    },
    LineSegments: class {
        constructor(geometry, material) {
            Object.assign(this, { geometry, material });
        }
    }
};

const expectedModels = [
    { type: "cesium-chloride", formula: "CsCl", cation: "Cs", anion: "Cl", count: 16, ratio: [8, 8], distanceFactor: Math.sqrt(3) / 2 },
    { type: "zincblende", formula: "GaAs", cation: "Ga", anion: "As", count: 64, ratio: [32, 32], distanceFactor: Math.sqrt(3) / 4 },
    { type: "fluorite", formula: "CeO₂", cation: "Ce", anion: "O", count: 96, ratio: [32, 64], distanceFactor: Math.sqrt(3) / 4 }
];

for (const model of expectedModels) {
    const latticeConstant = 5;
    const bondDistances = [];
    const group = new Group();
    const crystal = window.AtomViewCrystalRenderer.buildCubicCrystal({
        ...model,
        lattice_constant_angstrom: latticeConstant
    }, {
        THREE,
        moleculeGroup: group,
        createAtom: (element, position) => ({ element, position }),
        createBond: (start, end) => {
            bondDistances.push(Math.sqrt(start.distanceToSquared(end)));
            return [{}];
        },
        formula: model.formula
    });

    assert.equal(crystal.atoms.length, model.count, `${model.type} atom count`);
    assert.equal(crystal.atoms.filter(atom => atom.element === model.cation).length, model.ratio[0]);
    assert.equal(crystal.atoms.filter(atom => atom.element === model.anion).length, model.ratio[1]);
    assert.equal(crystal.bonds.length, bondDistances.length);
    assert.ok(bondDistances.length > 0, `${model.type} has coordination links`);
    for (const distance of bondDistances) {
        assert.ok(
            Math.abs(distance - model.distanceFactor * latticeConstant) < 1e-8,
            `${model.type} link should be at its prototype nearest-neighbor distance`
        );
    }
    assert.match(crystal.status, new RegExp(model.type));
    assert.ok(crystal.status.startsWith(`${model.formula} `));
    assert.ok(group.children.length > crystal.atoms.length);
}

const elementModels = require(path.join(__dirname, "..", "element_crystal_models.json"));
const expectedBasisCounts = {
    fcc: 4,
    bcc: 2,
    diamond: 8,
    hcp: 2,
    dhcp: 4,
    a7: 2,
    custom: null
};
for (const [atomicNumber, model] of Object.entries(elementModels)) {
    const group = new Group();
    const result = window.AtomViewCrystalRenderer.buildElementalCrystal(model, {
        THREE,
        moleculeGroup: group,
        createAtom: (element, position) => ({ element, position }),
        createBond: (start, end) => [{ start, end }]
    });
    const basisCount = expectedBasisCounts[model.prototype] ?? model.basis.length;
    assert.equal(result.atoms.length, basisCount * 8, `${model.phase} replicated basis count`);
    assert.ok(result.bonds.length > 0, `${model.phase} should show neighbor coordination`);
    assert.ok(result.atoms.every(atom =>
        [atom.position.x, atom.position.y, atom.position.z].every(Number.isFinite)
    ), `${model.phase} coordinates should be finite`);
    assert.ok(result.atoms.every(atom => atom.element === model.element));
    assert.match(result.status, new RegExp(model.phase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
    assert.match(result.status, /not a molecule or the featured compound/);
    if (model.source_cod_id) assert.match(result.status, new RegExp(`COD ${model.source_cod_id}`));
    assert.ok(group.children.some(child => child.geometry instanceof THREE.BufferGeometry));
    assert.ok(atomicNumber);
}

for (const element of Object.values(elementData).filter(
    item => item.crystal_structure?.type === "fractional-cell"
)) {
    const { molecule_formula: formula, crystal_structure: structure } = element;
    const group = new Group();
    const result = window.AtomViewCrystalRenderer.buildCubicCrystal(structure, {
        THREE,
        moleculeGroup: group,
        createAtom: (element, position) => ({ element, position }),
        createBond: (start, end) => [{ start, end }],
        formula
    });
    assert.equal(result.atoms.length, structure.basis.length * 8, `${formula} cell contents`);
    assert.ok(result.bonds.length > 0, `${formula} coordination links`);
    assert.match(result.status, new RegExp(`${formula} crystallographic cell`));
    assert.match(result.status, new RegExp(`COD ${structure.source_cod_id}`));
    assert.ok(group.children.some(child => child.geometry instanceof THREE.BufferGeometry));
}

const malformed = { type: "fluorite", cation: "Ce", anion: "O", lattice_constant_angstrom: 0 };
assert.throws(
    () => window.AtomViewCrystalRenderer.buildCubicCrystal(malformed, {
        THREE, moleculeGroup: new Group(), formula: "CeO₂"
    }),
    /incomplete or invalid/
);
assert.throws(
    () => window.AtomViewCrystalRenderer.buildCubicCrystal(
        { ...malformed, type: "unknown", lattice_constant_angstrom: 5 },
        { THREE, moleculeGroup: new Group(), formula: "CeO₂" }
    ),
    /Unsupported crystal prototype/
);
assert.throws(
    () => window.AtomViewCrystalRenderer.buildElementalCrystal({
        element: "Se",
        phase: "invalid selenium",
        prototype: "custom",
        a_angstrom: 4.3,
        c_angstrom: 4.89,
        alpha_degrees: 90,
        beta_degrees: 90,
        gamma_degrees: 120,
        basis: [[0, 0, 0]]
    }, { THREE, moleculeGroup: new Group(), createAtom: () => ({}), createBond: () => [] }),
    /Custom crystal cell parameters/
);
assert.throws(
    () => window.AtomViewCrystalRenderer.buildElementalCrystal({
        element: "As",
        phase: "invalid A7 arsenic",
        prototype: "a7",
        a_angstrom: 4.13,
        alpha_degrees: 1e-10,
        internal_u: 0.227
    }, { THREE, moleculeGroup: new Group(), createAtom: () => ({}), createBond: () => [] }),
    /valid cell/
);

const template = readFileSync(path.join(__dirname, "..", "pages", "element_template.html"), "utf8");
assert.match(template, /<script src="\.\.\/crystal-renderer\.js"><\/script>/);
console.log("Cubic crystal prototypes retain stoichiometry and nearest-neighbor geometry.");
