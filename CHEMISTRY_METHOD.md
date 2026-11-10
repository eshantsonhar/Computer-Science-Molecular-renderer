# Molecular geometry method, validation, and limits

## Representation contract

The website now distinguishes a 2D chemical depiction from a 3D conformer:

- The skeletal editor's screen positions are 2D drawing/layout coordinates. They describe the edited graph; they are not passed off as physical coordinates.
- Every validated graph receives an independent RDKit 2D layout and SVG depiction from that same sanitized molecular graph; it is not flattened from the 3D conformer.
- Active 3D views use the coordinates returned by `/api/geometry`. The Three.js layers only center, scale, rotate, and draw those coordinates; they do not adjust bond angles to make a molecule look more regular.
- Periodic-table examples not curated as discrete molecules are not drawn as isolated conformers. An ionic solid, extended network, or coordination crystal requires a suitable crystal/unit-cell representation and cannot be inferred from its empirical formula.
- The equilibrium simulator uses force-field conformers for molecular illustrations. Its concentration/collision animation is not molecular dynamics, a reaction mechanism, or a thermodynamic calculation.

Coordinates returned by the API are in ångströms.

## 3D generation pipeline

1. Interpret an IUPAC name locally with the vendored OPSIN 2.9.0 parser, then parse its isomeric SMILES with RDKit; direct SMILES, MDL Molfile, and atom/bond graph inputs are parsed by RDKit. Sanitize valence, aromaticity, charges, and connectivity.
2. Preserve input isotope, formal-charge, radical-electron, and supported stereochemical annotations. Add hydrogens using RDKit's valence model.
3. Generate a bounded, deterministic ETKDGv3 conformer ensemble (default eight conformers, fixed seed, single thread).
4. Minimize each conformer for up to 500 iterations with MMFF94s by default. If MMFF parameters are unavailable, automatic selection may use UFF; the response and UI identify this lower-confidence fallback.
5. Return the lowest finite-energy conformer found in that ensemble, connectivity, canonical isomeric SMILES, formula, optimization status, and explicit limitations.

The same validated, hydrogen-normalized molecular graph is separately depicted with RDKit's 2D coordinate generator and black-and-white SVG drawer. Inventory cards and reaction-step structures consume this server-generated SVG rather than redrawing a label or approximating the graph in the browser. The depiction is not a geometry measurement.

## Structure-to-name pipeline

OPSIN parses names into structures; it is not used as a structure-to-name generator. Structure naming uses Orthonym 1.1.0 locally, with its pinned OPSIN 2.9.0 and centres 1.2.1 resources. The Vercel Python 3.12 builder installs the exact NumPy 2.5.4, RDKit 2026.3.5, lxml 6.1.3, JPype1 1.7.1, and packaging 26.3 versions declared in `requirements.txt`; the build fetches and checksum-verifies the Java runtime and naming JARs. The function does not download naming code or resources at request time.

Orthonym's provenance tier is retained. A `pin_verified` or `systematic_verified` candidate is exposed as an IUPAC name only after the local OPSIN parser reconstructs the name and its canonical isomeric SMILES exactly matches the source graph. Unverified PIN/best-effort candidates are explicitly labeled and never promoted to verified IUPAC names. Unsupported structures, identity mismatches, and unavailable local resources yield `IUPAC name unavailable for this structure`.

The engine is rule-based and has bounded nomenclature coverage. Its presence does not imply a verified Preferred IUPAC Name for every structure. See [Orthonym v1.1.0](https://github.com/Steinbeck-Lab/Orthonym/tree/v1.1.0), its [output tiers](https://steinbeck-lab.github.io/Orthonym/guide/tiers.html), the [bundled runtime notices](api/vendor/orthonym_jars/NOTICE.md), and the [Organic Reactions evidence notes](docs/ORGANIC_REACTIONS_EVIDENCE.md) for provenance, licensing, deployment verification status, and limitations.

ETKDG is a distance-geometry conformer-generation method informed by experimental torsion preferences; it does not calculate an exact quantum-mechanical structure. Force-field minimization is an empirical model. Selecting the lowest energy among a finite set does not establish a global minimum, a unique conformer, or an experimentally observed geometry. Unspecified stereocentres do not acquire a chemically justified configuration merely because an embedding algorithm returns one; the UI warns when the input leaves them unspecified.

Requested spin multiplicities are validated for electron-count parity and reported, but RDKit's MMFF/UFF optimization is not spin-state-specific. Radical geometries therefore remain model-limited and are explicitly warned. Disconnected components are optimized without a predicted solvent, ion-pair, or crystal arrangement.

## Validation

`tests/test_geometry.py` covers methane, ethane, ethene, ethyne, water, ammonia, formaldehyde, carbon dioxide, aromatic and substituted rings, ethanol, amines, amides, acids, esters, formal charges, a radical, halogens, stereochemistry, conjugation, branched chains, cyclopropane through cyclohexane, fused and bridged rings, a macrocycle, and a long-chain conformer. It checks finite nondegenerate coordinates, selected reference bond angles, selected torsions, supported charge/radical/stereo data, and explicit failure for unsupported chemistry. IUPAC tests cover branched alcohols, substituted aromatics, amides, stereochemical names, and rejected names. A UFF phosphorus pentafluoride test checks trigonal-bipyramidal angles. Sulfur hexafluoride is intentionally rejected because neither supported force field has complete parameters for it. HTTP tests exercise the function's health response, IUPAC and SMILES geometry responses, malformed JSON, and invalid chemistry error status.

For the fixed default seed and two-conformer test runs, selected generated angles (degrees) are:

| Structure and angle | Generated | Approximate gas-phase reference |
|---|---:|---:|
| H₂O, H–O–H | 103.98 | 104.5 |
| NH₃, H–N–H | 106.00 | 106.7 |
| CH₄, H–C–H | 109.47 | 109.47 |
| CO₂, O–C–O | 180.00 | 180 |
| C₂H₂, C–C–H | 180.00 | 180 |
| Benzene, C–C–C | 120.00 | 120 |
| Cyclopropane, C–C–C | 60.00 | 60 |
| Cyclobutane, ring C–C–C | 87.16 | about 88 |
| Cyclopentane, ring C–C–C | 106.34 | about 105 |
| Cyclohexane, ring C–C–C | 111.64 | about 112 |
| n-Butane, C–C–C | 111.49 | about 112 |
| Ethene, C–C–H | 121.05 | about 122 |
| Formaldehyde, H–C–H | 115.53 | about 116 |

These are representative checks, not a universal error bound. Experimental values depend on the molecular state and measurement/model convention; ring angles depend on conformation. The tolerances are limited to these named tests and must not be generalized to arbitrary molecules. Cyclohexane ring torsions are also checked for a chair-like conformer, and n-butane for a staggered low-energy conformer.

For the fixed seed, the eight-conformer torsion checks produced:

| Structure and torsion | Generated |
|---|---:|
| Cyclohexane, six successive ring C–C–C–C torsions | 54.26° each |
| n-Butane, central C–C–C–C torsion | 180.00° |

Reference conventions and experimental/computational geometry data are available through the [NIST Computational Chemistry Comparison and Benchmark Database (CCCBDB)](https://cccbdb.nist.gov/), particularly its [experimental geometries](https://cccbdb.nist.gov/expgeom1x.asp) and [bond/angle comparisons](https://cccbdb.nist.gov/compgeom1x.asp). CCCBDB cautions that experimental equilibrium (`r_e`) and vibrationally averaged (`r_0`) geometries are not interchangeable, and that atom mappings can affect comparisons. The small-molecule values above are approximate checks, not a bulk benchmark against a single uniform experimental dataset.

## Website pathways

- The main renderer uses one input field with a format dropdown for IUPAC names, SMILES, and Molfiles. IUPAC names are sent only to this site's same-origin geometry endpoint, where the repository's OPSIN Java bridge resolves the name locally to SMILES before RDKit generates geometry. No external chemistry API or separate name-parsing service is used. OPSIN warnings are surfaced with the geometry limitations. Unsupported or uninterpretable names fail explicitly. Advanced JSON and editor graphs continue through the same endpoint.
- All 118 generated element pages share the updated template. Only the curated discrete examples H₂O, H₃BO₃, CO₂, NH₃, and HF are eligible for conformer generation. Most other examples represent solids, ionic compounds, coordination/extended structures, or lack validated topology/parameters and are explicitly not displayed as molecule geometries.
- The equilibrium simulator validates each species graph against its displayed formula before enabling a reaction. Incorrect source connectivity discovered in the esterification and sulfur-trioxide data was corrected. Reaction species that fail validation leave the simulation disabled.
- Four unlinked standalone renderer pages redirect to the canonical renderer; the old equilibrium editor redirects to the current simulator.

## Known limitations and unsupported domains

- MMFF94s and UFF are not quantum chemistry or experimental structure determination. The site does not provide universal angle accuracy or a claim that every force-field minimum is physically correct.
- No solvent, temperature-dependent ensemble, protein environment, crystal packing, periodic boundary conditions, transition-metal coordination model, or quantum-chemical calculation is supplied.
- UFF coverage does not imply reliable accuracy for every inorganic or hypervalent species. Missing parameters cause an explicit error rather than a guessed structure.
- The periodic-table section intentionally omits most solid/ionic examples from 3D molecular rendering until validated crystal structures and an appropriate crystal renderer are available.
- The editor does not encode charges, isotopes, or stereochemistry. SMILES and Molfile input are required when those distinctions matter.
- OPSIN supports a broad range of systematic organic names, but it is not a universal chemical-name resolver. Some inorganic, coordination, ambiguous, or nonstandard names may be unsupported; OPSIN warnings are included in the response. Enter SMILES or a Molfile when the exact connectivity, charge, isotope, or stereochemistry must be explicit.
- Structures are limited to 150 heavy atoms, at most 20 conformers per request, and a 1 MB request body. Large, highly flexible, unusual, or unsupported molecules may be slow or rejected.
- A fixed seed improves reproducibility for the pinned RDKit build; results can change across RDKit releases, parameter sets, or requested conformer counts.

## Organic reaction planning

The Organic Reactions section is separate from the molecular geometry method. It uses sanitized RDKit molecular graphs, explicit reactant inventories, narrowly encoded transformations, finite reagent equivalents, complete coproduct graphs, and atom-level source identifiers. It checks product valence/sanitization, atom/isotope counts, total formal charge, atom provenance, and target stereochemical identity. Successful graph generation is not treated as proof that a reaction occurs.

The locally implemented knowledge base contains twelve constrained rules, grouped around acyl substitution and acid-chloride formation, ester saponification/acidification, alkene hydrogenation, reductive ozonolysis, and peroxide-promoted HBr addition. Each rule has a substrate matcher, graph executor, required reagents/conditions, balancing checks, evidence references, and explicit limits; the catalog is not a general reaction database. The planner uses bounded best-first search over finite starting-material inventories and applies only rules authorized by the selected reagent mode. Route ranking is limited to reaction count, stoichiometric equivalents, listed conditions, and stable rule ordering. A `no-supported-route` result is not a claim that a target is chemically unreachable. See [the chemistry study](./docs/ORGANIC_REACTIONS_CHEMISTRY_STUDY.md) and [reaction evidence](./docs/ORGANIC_REACTIONS_EVIDENCE.md) for rule-specific scope and citations.

The textbook sources provide educational coverage, not validation of arbitrary substrates or optimized experimental procedures. Conditions in the catalog are qualitative; integer quantities are finite stoichiometric bookkeeping units, not measured moles, mass, or an experimental plan. The planner predicts neither rates, yields, equilibria, safety, competition from unmodeled species, nor experimental success. Valid graph execution and atom accounting do not establish experimental feasibility.

`api/geometry.py` also returns molecular weight, total formal charge, and assigned atom/bond stereochemistry in metadata for the organic compound lists. This descriptive metadata does not make the conformer geometry or planner output an experimental measurement.

## Technical and scientific sources

- [RDKit: Getting Started in Python](https://www.rdkit.org/docs/GettingStartedInPython.html) — SMILES/Molfile parsing and molecular representation.
- [RDKit distance geometry module](https://www.rdkit.org/docs/source/rdkit.Chem.rdDistGeom.html) — ETKDG variants, including ETKDGv3.
- [RDKit force-field helpers](https://www.rdkit.org/docs/source/rdkit.Chem.rdForceFieldHelpers.html) — MMFF94/MMFF94s and UFF parameter availability and minimization.
- [OPSIN 2.9.0](https://github.com/dan2097/opsin/tree/2.9.0) — locally bundled IUPAC name-to-structure parser, resources, and API.
- Lowe, D. M.; Corbett, P. T.; Murray-Rust, P.; Glen, R. C. “Chemical name to structure: OPSIN, an open source solution.” *J. Chem. Inf. Model.* (2011). [doi:10.1021/ci100384d](https://doi.org/10.1021/ci100384d).
- Riniker, S.; Landrum, G. A. “Better Informed Distance Geometry: Using What We Know To Improve Conformation Generation.” *J. Chem. Inf. Model.* (2015). [doi:10.1021/acs.jcim.5b00654](https://doi.org/10.1021/acs.jcim.5b00654).
- Halgren, T. A. “Merck Molecular Force Field. I. Basis, Form, Scope, Parameterization, and Performance of MMFF94.” *J. Comput. Chem.* (1996). [doi:10.1002/(SICI)1096-987X(199604)17:5/6%3C490::AID-JCC1%3E3.0.CO;2-P](https://doi.org/10.1002/(SICI)1096-987X(199604)17:5/6%3C490::AID-JCC1%3E3.0.CO;2-P).
