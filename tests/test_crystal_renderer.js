const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

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
    LineSegments: class {
        constructor(geometry, material) {
            Object.assign(this, { geometry, material });
        }
    }
};

const expectedModels = [
    { type: "cesium-chloride", cation: "Cs", anion: "Cl", count: 16, ratio: [8, 8], distanceFactor: Math.sqrt(3) / 2 },
    { type: "zincblende", cation: "Ga", anion: "As", count: 64, ratio: [32, 32], distanceFactor: Math.sqrt(3) / 4 },
    { type: "fluorite", cation: "Ce", anion: "O", count: 96, ratio: [32, 64], distanceFactor: Math.sqrt(3) / 4 }
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
        }
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
    assert.ok(group.children.length > crystal.atoms.length);
}

const malformed = { type: "fluorite", cation: "Ce", anion: "O", lattice_constant_angstrom: 0 };
assert.throws(
    () => window.AtomViewCrystalRenderer.buildCubicCrystal(malformed, { THREE, moleculeGroup: new Group() }),
    /incomplete or invalid/
);
assert.throws(
    () => window.AtomViewCrystalRenderer.buildCubicCrystal(
        { ...malformed, type: "unknown", lattice_constant_angstrom: 5 },
        { THREE, moleculeGroup: new Group() }
    ),
    /Unsupported crystal prototype/
);

const template = readFileSync(path.join(__dirname, "..", "pages", "element_template.html"), "utf8");
assert.match(template, /<script src="\.\.\/crystal-renderer\.js"><\/script>/);
console.log("Cubic crystal prototypes retain stoichiometry and nearest-neighbor geometry.");
