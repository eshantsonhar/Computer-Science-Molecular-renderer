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

    function buildCubicCrystal(structure, { THREE, moleculeGroup, createAtom, createBond, formula }) {
        if (structure?.type === 'fractional-cell') {
            return buildFractionalCellCrystal(structure, {
                THREE,
                moleculeGroup,
                createAtom,
                createBond,
                formula
            });
        }
        const { type, cation, anion, lattice_constant_angstrom: latticeConstant } = structure || {};
        if (
            typeof cation !== 'string' ||
            typeof anion !== 'string' ||
            cation === anion ||
            !Number.isFinite(latticeConstant) ||
            latticeConstant <= 0 ||
            typeof formula !== 'string' ||
            formula.trim() === ''
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
                `${formula} ${prototype.name} crystal fragment; cubic lattice constant ${latticeConstant} Å. ` +
                'Lines show nearest-neighbor coordination, not necessarily covalent bonds; periodic links across the fragment boundary are omitted.'
        };
    }

    function getElementalBasis(structure) {
        if (structure.prototype === 'fcc') {
            return {
                vectors: [
                    [structure.a_angstrom, 0, 0],
                    [0, structure.a_angstrom, 0],
                    [0, 0, structure.a_angstrom]
                ],
                basis: faceCenteredCubicSites
            };
        }

        if (structure.prototype === 'bcc') {
            return {
                vectors: [
                    [structure.a_angstrom, 0, 0],
                    [0, structure.a_angstrom, 0],
                    [0, 0, structure.a_angstrom]
                ],
                basis: [[0, 0, 0], [0.5, 0.5, 0.5]]
            };
        }

        if (structure.prototype === 'diamond') {
            return {
                vectors: [
                    [structure.a_angstrom, 0, 0],
                    [0, structure.a_angstrom, 0],
                    [0, 0, structure.a_angstrom]
                ],
                basis: [
                    ...faceCenteredCubicSites,
                    [0.25, 0.25, 0.25],
                    [0.25, 0.75, 0.75],
                    [0.75, 0.25, 0.75],
                    [0.75, 0.75, 0.25]
                ]
            };
        }

        if (structure.prototype === 'hcp' || structure.prototype === 'dhcp') {
            const a = structure.a_angstrom;
            const c = structure.c_angstrom;
            const basis = structure.prototype === 'hcp'
                ? [[0, 0, 0], [2 / 3, 1 / 3, 0.5]]
                : [[0, 0, 0], [2 / 3, 1 / 3, 0.25], [0, 0, 0.5], [1 / 3, 2 / 3, 0.75]];
            return {
                vectors: [
                    [a, 0, 0],
                    [-a / 2, Math.sqrt(3) * a / 2, 0],
                    [0, 0, c]
                ],
                basis
            };
        }

        if (structure.prototype === 'a7') {
            const a = structure.a_angstrom;
            const alpha = structure.alpha_degrees * Math.PI / 180;
            return {
                vectors: [
                    [a, 0, 0],
                    [a * Math.cos(alpha), a * Math.sin(alpha), 0],
                    [
                        a * Math.cos(alpha),
                        a * (Math.cos(alpha) - Math.cos(alpha) ** 2) / Math.sin(alpha),
                        a * Math.sqrt(1 - Math.cos(alpha) ** 2 -
                            ((Math.cos(alpha) - Math.cos(alpha) ** 2) / Math.sin(alpha)) ** 2)
                    ]
                ],
                basis: [[0, 0, 0], [structure.internal_u, structure.internal_u, structure.internal_u]]
            };
        }

        if (structure.prototype === 'custom') {
            const { a_angstrom: a, b_angstrom: b, c_angstrom: c } = structure;
            const alpha = structure.alpha_degrees * Math.PI / 180;
            const beta = structure.beta_degrees * Math.PI / 180;
            const gamma = structure.gamma_degrees * Math.PI / 180;
            const sinGamma = Math.sin(gamma);
            const cX = c * Math.cos(beta);
            const cY = c * (Math.cos(alpha) - Math.cos(beta) * Math.cos(gamma)) / sinGamma;
            const cZSquared = c ** 2 - cX ** 2 - cY ** 2;
            if (!Number.isFinite(cZSquared) || cZSquared <= 0) {
                throw new Error('Element crystal cell parameters do not define a valid cell.');
            }
            return {
                vectors: [
                    [a, 0, 0],
                    [b * Math.cos(gamma), b * sinGamma, 0],
                    [cX, cY, Math.sqrt(cZSquared)]
                ],
                basis: structure.basis
            };
        }

        throw new Error(`Unsupported elemental crystal prototype: ${structure.prototype}.`);
    }

    function cartesian(fractional, vectors) {
        return [
            fractional[0] * vectors[0][0] + fractional[1] * vectors[1][0] + fractional[2] * vectors[2][0],
            fractional[0] * vectors[0][1] + fractional[1] * vectors[1][1] + fractional[2] * vectors[2][1],
            fractional[0] * vectors[0][2] + fractional[1] * vectors[1][2] + fractional[2] * vectors[2][2]
        ];
    }

    function latticeVectors(parameters) {
        const { a, b = a, c, alpha = 90, beta = 90, gamma = 90 } = parameters || {};
        if (![a, b, c, alpha, beta, gamma].every(Number.isFinite) || a <= 0 || b <= 0 || c <= 0) {
            throw new Error('Crystal lattice parameters are incomplete or invalid.');
        }
        if ([alpha, beta, gamma].some(angle => angle <= 0 || angle >= 180)) {
            throw new Error('Crystal lattice angles do not define a valid cell.');
        }
        const alphaRadians = alpha * Math.PI / 180;
        const betaRadians = beta * Math.PI / 180;
        const gammaRadians = gamma * Math.PI / 180;
        const sinGamma = Math.sin(gammaRadians);
        if (Math.abs(sinGamma) < 1e-8) throw new Error('Crystal lattice angles do not define a valid cell.');
        const cX = c * Math.cos(betaRadians);
        const cY = c * (Math.cos(alphaRadians) -
            Math.cos(betaRadians) * Math.cos(gammaRadians)) / sinGamma;
        const cZSquared = c ** 2 - cX ** 2 - cY ** 2;
        if (!Number.isFinite(cZSquared) || cZSquared <= 0) {
            throw new Error('Crystal lattice angles do not define a valid cell.');
        }
        return [
            [a, 0, 0],
            [b * Math.cos(gammaRadians), b * sinGamma, 0],
            [cX, cY, Math.sqrt(cZSquared)]
        ];
    }

    function addCrystalFrame({ THREE, moleculeGroup, vectors, repeats }) {
        const corners = [];
        for (let mask = 0; mask < 8; mask += 1) {
            corners.push(cartesian([
                mask & 1 ? repeats[0] : 0,
                mask & 2 ? repeats[1] : 0,
                mask & 4 ? repeats[2] : 0
            ], vectors));
        }
        const framePoints = [];
        for (let corner = 0; corner < 8; corner += 1) {
            for (const axisMask of [1, 2, 4]) {
                if (corner & axisMask) continue;
                framePoints.push(new THREE.Vector3(...corners[corner]));
                framePoints.push(new THREE.Vector3(...corners[corner | axisMask]));
            }
        }
        const geometry = new THREE.BufferGeometry().setFromPoints(framePoints);
        moleculeGroup.add(new THREE.LineSegments(
            geometry,
            new THREE.LineBasicMaterial({ color: 0x65758b })
        ));
    }

    function buildFractionalCellCrystal(structure, { THREE, moleculeGroup, createAtom, createBond, formula }) {
        const { basis, lattice_parameters_angstrom: parameters, source_cod_id: codId, space_group: spaceGroup } = structure;
        if (
            typeof formula !== 'string' ||
            !Array.isArray(basis) ||
            basis.length === 0 ||
            basis.some(site =>
                !site ||
                typeof site.element !== 'string' ||
                !Array.isArray(site.fractional) ||
                site.fractional.length !== 3 ||
                site.fractional.some(value => !Number.isFinite(value))
            )
        ) {
            throw new Error('Fractional crystal structure data is incomplete or invalid.');
        }
        const vectors = latticeVectors(parameters);
        const repeatCounts = [2, 2, 2];
        const atoms = [];
        const bonds = [];
        const sites = [];

        moleculeGroup.clear();
        for (let cellA = 0; cellA < repeatCounts[0]; cellA += 1) {
            for (let cellB = 0; cellB < repeatCounts[1]; cellB += 1) {
                for (let cellC = 0; cellC < repeatCounts[2]; cellC += 1) {
                    for (const site of basis) {
                        const position = new THREE.Vector3(...cartesian([
                            cellA + site.fractional[0],
                            cellB + site.fractional[1],
                            cellC + site.fractional[2]
                        ], vectors));
                        moleculeGroup.add(createAtom(site.element, position));
                        sites.push({ element: site.element, position });
                        atoms.push({ element: site.element, position });
                    }
                }
            }
        }

        let nearestUnlikeNeighborSquared = Infinity;
        for (let first = 0; first < basis.length; first += 1) {
            for (let second = 0; second < basis.length; second += 1) {
                if (basis[first].element === basis[second].element) continue;
                for (let shiftA = -1; shiftA <= 1; shiftA += 1) {
                    for (let shiftB = -1; shiftB <= 1; shiftB += 1) {
                        for (let shiftC = -1; shiftC <= 1; shiftC += 1) {
                            const firstPosition = cartesian(basis[first].fractional, vectors);
                            const secondPosition = cartesian([
                                basis[second].fractional[0] + shiftA,
                                basis[second].fractional[1] + shiftB,
                                basis[second].fractional[2] + shiftC
                            ], vectors);
                            const squared = (firstPosition[0] - secondPosition[0]) ** 2 +
                                (firstPosition[1] - secondPosition[1]) ** 2 +
                                (firstPosition[2] - secondPosition[2]) ** 2;
                            nearestUnlikeNeighborSquared = Math.min(nearestUnlikeNeighborSquared, squared);
                        }
                    }
                }
            }
        }
        if (!Number.isFinite(nearestUnlikeNeighborSquared) || nearestUnlikeNeighborSquared <= 0) {
            throw new Error('Crystal structure has no valid unlike-element coordination distance.');
        }

        for (let first = 0; first < sites.length; first += 1) {
            for (let second = first + 1; second < sites.length; second += 1) {
                if (sites[first].element === sites[second].element) continue;
                if (sites[first].position.distanceToSquared(sites[second].position) >
                    nearestUnlikeNeighborSquared * 1.0001) continue;
                createBond(sites[first].position, sites[second].position)
                    .forEach(mesh => {
                        moleculeGroup.add(mesh);
                        bonds.push(mesh);
                    });
            }
        }

        addCrystalFrame({
            THREE,
            moleculeGroup,
            vectors,
            repeats: repeatCounts
        });
        const cellParameters = ['a', 'b', 'c']
            .map(axis => `${axis}=${parameters[axis] ?? parameters.a} Å`)
            .join(', ');
        return {
            atoms,
            bonds,
            status:
                `${formula} crystallographic cell${spaceGroup ? ` (${spaceGroup})` : ''}; ${cellParameters}, ` +
                `2×2×2 fragment${codId ? `, COD ${codId}` : ''}. ` +
                'Lines show nearest-neighbor coordination, not necessarily covalent bonds.'
        };
    }

    function buildElementalCrystal(structure, { THREE, moleculeGroup, createAtom, createBond }) {
        if (
            !structure ||
            typeof structure.element !== 'string' ||
            typeof structure.phase !== 'string' ||
            typeof structure.prototype !== 'string' ||
            !Number.isFinite(structure.a_angstrom) ||
            structure.a_angstrom <= 0
        ) {
            throw new Error('Elemental crystal structure data is incomplete or invalid.');
        }
        if (
            ['hcp', 'dhcp'].includes(structure.prototype) &&
            (!Number.isFinite(structure.c_angstrom) || structure.c_angstrom <= 0)
        ) {
            throw new Error('Hexagonal crystal structure data needs a positive c lattice parameter.');
        }
        if (
            structure.prototype === 'a7' &&
            (!Number.isFinite(structure.alpha_degrees) ||
                structure.alpha_degrees <= 0 ||
                structure.alpha_degrees >= 120 ||
                !Number.isFinite(structure.internal_u) ||
                structure.internal_u <= 0 ||
                structure.internal_u >= 0.5)
        ) {
            throw new Error('A7 crystal structure internal coordinates are invalid.');
        }
        if (structure.prototype === 'custom') {
            const parameters = [
                structure.a_angstrom,
                structure.b_angstrom,
                structure.c_angstrom,
                structure.alpha_degrees,
                structure.beta_degrees,
                structure.gamma_degrees
            ];
            if (
                !parameters.every(Number.isFinite) ||
                parameters.slice(0, 3).some(value => value <= 0) ||
                parameters.slice(3).some(value => value <= 0 || value >= 180)
            ) {
                throw new Error('Custom crystal cell parameters are incomplete or invalid.');
            }
        }

        const { vectors, basis } = getElementalBasis(structure);
        const validVectors = Array.isArray(vectors) &&
            vectors.length === 3 &&
            vectors.every(vector =>
                Array.isArray(vector) &&
                vector.length === 3 &&
                vector.every(Number.isFinite)
            );
        if (!validVectors) {
            throw new Error('Elemental crystal cell vectors are invalid.');
        }
        const [vectorA, vectorB, vectorC] = vectors;
        const cellVolume =
            vectorA[0] * (vectorB[1] * vectorC[2] - vectorB[2] * vectorC[1]) -
            vectorA[1] * (vectorB[0] * vectorC[2] - vectorB[2] * vectorC[0]) +
            vectorA[2] * (vectorB[0] * vectorC[1] - vectorB[1] * vectorC[0]);
        if (!Number.isFinite(cellVolume) || cellVolume <= 0) {
            throw new Error('Elemental crystal cell parameters do not define a valid cell.');
        }
        if (
            !Array.isArray(basis) ||
            basis.length === 0 ||
            basis.some(position =>
                !Array.isArray(position) ||
                position.length !== 3 ||
                position.some(value => !Number.isFinite(value))
            )
        ) {
            throw new Error('Elemental crystal basis positions are invalid.');
        }

        let nearestNeighborSquared = Infinity;
        const unitCellSites = basis.map(position => cartesian(position, vectors));
        for (let first = 0; first < basis.length; first += 1) {
            for (let second = 0; second < basis.length; second += 1) {
                for (let shiftA = -1; shiftA <= 1; shiftA += 1) {
                    for (let shiftB = -1; shiftB <= 1; shiftB += 1) {
                        for (let shiftC = -1; shiftC <= 1; shiftC += 1) {
                            if (first === second && shiftA === 0 && shiftB === 0 && shiftC === 0) continue;
                            const neighbor = cartesian([
                                basis[second][0] + shiftA,
                                basis[second][1] + shiftB,
                                basis[second][2] + shiftC
                            ], vectors);
                            const distanceSquared = (unitCellSites[first][0] - neighbor[0]) ** 2 +
                                (unitCellSites[first][1] - neighbor[1]) ** 2 +
                                (unitCellSites[first][2] - neighbor[2]) ** 2;
                            nearestNeighborSquared = Math.min(nearestNeighborSquared, distanceSquared);
                        }
                    }
                }
            }
        }
        if (!Number.isFinite(nearestNeighborSquared) || nearestNeighborSquared <= 0) {
            throw new Error('Elemental crystal basis has no valid nearest-neighbor distance.');
        }

        const sites = [];
        const atoms = [];
        const bonds = [];
        moleculeGroup.clear();
        for (let cellA = 0; cellA < 2; cellA += 1) {
            for (let cellB = 0; cellB < 2; cellB += 1) {
                for (let cellC = 0; cellC < 2; cellC += 1) {
                    for (const fractional of basis) {
                        const coordinates = cartesian([
                            cellA + fractional[0],
                            cellB + fractional[1],
                            cellC + fractional[2]
                        ], vectors);
                        const position = new THREE.Vector3(...coordinates);
                        moleculeGroup.add(createAtom(structure.element, position));
                        sites.push({ element: structure.element, position });
                        atoms.push({ element: structure.element, position });
                    }
                }
            }
        }

        const toleranceSquared = nearestNeighborSquared * 1.0001;
        for (let first = 0; first < sites.length; first += 1) {
            for (let second = first + 1; second < sites.length; second += 1) {
                if (sites[first].position.distanceToSquared(sites[second].position) > toleranceSquared) continue;
                createBond(sites[first].position, sites[second].position)
                    .forEach(mesh => {
                        moleculeGroup.add(mesh);
                        bonds.push(mesh);
                    });
            }
        }

        addCrystalFrame({ THREE, moleculeGroup, vectors, repeats: [2, 2, 2] });

        const cellParameters = structure.c_angstrom
            ? `a=${structure.a_angstrom} Å, c=${structure.c_angstrom} Å`
            : structure.prototype === 'a7'
                ? `a=${structure.a_angstrom} Å, alpha=${structure.alpha_degrees}°`
                : `a=${structure.a_angstrom} Å`;
        return {
            atoms,
            bonds,
            status:
                `Shown: ${structure.phase} elemental crystal (${structure.prototype}); ${cellParameters}, 2×2×2 unit-cell fragment. ` +
                `This is an elemental solid phase, not a molecule or the featured compound described on this page.` +
                `${structure.source_cod_id ? ` Crystallographic source: COD ${structure.source_cod_id}.` : ''} ` +
                'Lines indicate nearest-neighbor coordination, not covalent bonds.'
        };
    }

    window.AtomViewCrystalRenderer = { buildCubicCrystal, buildElementalCrystal };
})();
