(function () {
    const faceCenteredCubicSites = [
        [0, 0, 0],
        [0, 0.5, 0.5],
        [0.5, 0, 0.5],
        [0.5, 0.5, 0]
    ];

    function getCrystalBasis(type, cation, anion) {
        if (type === 'cesium-chloride') {
            return {
                name: 'cesium-chloride',
                nearestNeighborFactor: Math.sqrt(3) / 2,
                sites: [
                    { element: cation, fractional: [0, 0, 0] },
                    { element: anion, fractional: [0.5, 0.5, 0.5] }
                ]
            };
        }

        if (type === 'zincblende') {
            return {
                name: 'zincblende',
                nearestNeighborFactor: Math.sqrt(3) / 4,
                sites: [
                    ...faceCenteredCubicSites.map(fractional => ({ element: cation, fractional })),
                    { element: anion, fractional: [0.25, 0.25, 0.25] },
                    { element: anion, fractional: [0.25, 0.75, 0.75] },
                    { element: anion, fractional: [0.75, 0.25, 0.75] },
                    { element: anion, fractional: [0.75, 0.75, 0.25] }
                ]
            };
        }

        if (type === 'fluorite') {
            return {
                name: 'fluorite',
                nearestNeighborFactor: Math.sqrt(3) / 4,
                sites: [
                    ...faceCenteredCubicSites.map(fractional => ({ element: cation, fractional })),
                    ...[0.25, 0.75].flatMap(x =>
                        [0.25, 0.75].flatMap(y =>
                            [0.25, 0.75].map(z => ({ element: anion, fractional: [x, y, z] }))
                        )
                    )
                ]
            };
        }

        throw new Error(`Unsupported crystal prototype: ${type}.`);
    }

    function buildCubicCrystal(structure, { THREE, moleculeGroup, createAtom, createBond }) {
        const { type, cation, anion, lattice_constant_angstrom: latticeConstant } = structure || {};
        if (
            typeof cation !== 'string' ||
            typeof anion !== 'string' ||
            cation === anion ||
            !Number.isFinite(latticeConstant) ||
            latticeConstant <= 0
        ) {
            throw new Error('Crystal structure data is incomplete or invalid.');
        }

        const prototype = getCrystalBasis(type, cation, anion);
        const offsets = [0, 1, 2].map(axis =>
            (1 + Math.max(...prototype.sites.map(site => site.fractional[axis]))) / 2
        );
        const sites = [];
        const atoms = [];
        const bonds = [];
        moleculeGroup.clear();

        for (let cellX = 0; cellX < 2; cellX += 1) {
            for (let cellY = 0; cellY < 2; cellY += 1) {
                for (let cellZ = 0; cellZ < 2; cellZ += 1) {
                    for (const site of prototype.sites) {
                        const position = new THREE.Vector3(
                            (cellX + site.fractional[0] - offsets[0]) * latticeConstant,
                            (cellY + site.fractional[1] - offsets[1]) * latticeConstant,
                            (cellZ + site.fractional[2] - offsets[2]) * latticeConstant
                        );
                        moleculeGroup.add(createAtom(site.element, position));
                        sites.push({ element: site.element, position });
                        atoms.push({ element: site.element, position });
                    }
                }
            }
        }

        const nearestNeighborDistance = prototype.nearestNeighborFactor * latticeConstant;
        const maxBondDistanceSquared = nearestNeighborDistance ** 2 * 1.0001;
        for (let first = 0; first < sites.length; first += 1) {
            for (let second = first + 1; second < sites.length; second += 1) {
                if (sites[first].element === sites[second].element) continue;
                if (sites[first].position.distanceToSquared(sites[second].position) > maxBondDistanceSquared) {
                    continue;
                }
                const meshes = createBond(sites[first].position, sites[second].position);
                meshes.forEach(mesh => {
                    moleculeGroup.add(mesh);
                    bonds.push(mesh);
                });
            }
        }

        moleculeGroup.add(new THREE.LineSegments(
            new THREE.EdgesGeometry(new THREE.BoxGeometry(
                latticeConstant * 2,
                latticeConstant * 2,
                latticeConstant * 2
            )),
            new THREE.LineBasicMaterial({ color: 0x65758b })
        ));

        return {
            atoms,
            bonds,
            status:
                `${cation}${anion} ${prototype.name} crystal fragment; cubic lattice constant ${latticeConstant} Å. ` +
                'Lines show nearest-neighbor coordination, not necessarily covalent bonds; periodic links across the fragment boundary are omitted.'
        };
    }

    window.AtomViewCrystalRenderer = { buildCubicCrystal };
})();
