# Main renderer: molecular compatibility audit

Audit status: **in progress; no universal chemical compatibility claim.** Production observations below were made on 2026-11-10 against `https://atom-view.vercel.app/`. Local chemistry tests ran with RDKit 2026.09.1; the deployed function reports its own RDKit-generated output and is pinned separately.

## Exact phosphorus-containing input

The supplied IUPAC name was submitted unchanged to the production renderer. The exact request was:

```json
{
  "iupacName": "({[({[(2R,3S,4R,5R)-5-(6-amino-9H-purin-9-yl)-3,4-dihydroxyoxolan-2-yl]methoxy}(hydroxy)phosphoryl)oxy](hydroxy)phosphoryl}oxy)phosphonic acid",
  "conformers": 2
}
```

`POST /api/geometry` returned HTTP 200. The response identifies `C10H16N5O13P3`, net charge 0, 47 atoms including 16 added hydrogens, 49 bonds, canonical isomeric SMILES `Nc1ncnc2c1ncn2[C@@H]1O[C@H](COP(=O)(O)OP(=O)(O)OP(=O)(O)O)[C@@H](O)[C@H]1O`, and MMFF94s optimization. The four name-specified sugar stereocentres were retained as R,R,S,R in graph-index order and stereochemistry verification passed. Two additional stereogenic phosphorus centres remain unspecified by the name; the endpoint reports that explicitly instead of asserting a unique stereoisomer.

The 3D response included finite coordinates and a 2D SVG. The live main page rendered the molecule and reported 10 carbon, 16 hydrogen, 21 other atoms, and 49 bonds. After the palette change deployed, I reran the exact name in the Production browser: the canvas rendered the molecule, the counts were unchanged, and the three phosphorus atoms appeared in orange. I also submitted the same molecular identity through SMILES and a V2000 Molfile to production; both returned HTTP 200 and the same canonical isomeric SMILES, formula, charge, atom count, and bond count. Local regressions exercise IUPAC, SMILES, Molfile, and the general atom/bond graph input with the same expected graph.

The structure was independently compared with PubChem CID 5957 (adenosine 5'-triphosphate, neutral acid form). PubChem reports the same formula and its isomeric SMILES canonicalizes with local RDKit to the exact same stereochemical graph. This input is the neutral triphosphoric-acid form, not physiological ATP(4-); charged phosphate chains, including an ATP(4-) representation, are tested separately.

The exact molecule does **not** currently reproduce an input, sanitization, hydrogen-addition, conformer-generation, force-field, serialization, or HTTP failure in production. The historical failure stage cannot be established from the present successful reproduction. A concrete display defect was confirmed: phosphorus had no dedicated renderer color/radius and therefore used the generic gray fallback. The main renderer now gives phosphorus and other tested heteroatoms explicit palette/radius entries; computed atomic numbers are passed through to atom selection rather than inferred from a partial frontend table.

## Persistent stress corpus and observed results

[`tests/renderer_compatibility_corpus.py`](../tests/renderer_compatibility_corpus.py) defines 224 distinct stereochemical-isomeric SMILES cases. [`tests/test_renderer_compatibility.py`](../tests/test_renderer_compatibility.py) sends each through the actual geometry producer with one ETKDGv3 conformer and checks canonical identity, formula, net charge, heavy-atom count, explicit-hydrogen atom/bond counts, specified tetrahedral stereochemistry, SVG presence, finite coordinates, and non-degenerate bond lengths. All 224 passed locally.

| Category | Distinct structures |
|---|---:|
| Straight and branched alkanes | 31 |
| Alkenes and alkene stereoisomers | 13 |
| Alkynes | 8 |
| Cyclic, fused, and bridged hydrocarbons | 10 |
| Alcohols, ethers, carbonyls, acids, esters, amides, amines, nitriles, halides, nitro, sulfur groups, and epoxides | 30 |
| Aromatic and fused heterocycles | 36 |
| Phosphines, oxides, phosphates, phosphonates, phosphoramidates, polyphosphates, charged phosphates, and nucleotide forms | 38 |
| Boron, silicon, and other unusual element compounds | 16 |
| Additional heavier heteroatoms (Ge, As, Se, Sn, Te) | 7 |
| Ions, zwitterions, and multi-charge structures | 13 |
| Stereochemical amino acids, peptides, sugars, and nucleosides | 22 |
| **Total** | **224** |

Separate focused cases verify the exact named triphosphate across four input representations, boronic-acid and dimethyl-selenide UFF fallback with an explicit warning, charged phosphate identity, phosphorus hypervalence, invalid input handling, and geometry-limit error classification. This is a reproducible compatibility sample, not exhaustive coverage of the chemical universe or a physical validation of force-field accuracy.

## Pipeline and support boundary

The main IUPAC, SMILES, Molfile, editor graph, and advanced molecular-graph routes converge on the geometry endpoint. IUPAC is parsed locally by OPSIN 2.9.0 into RDKit; structures are sanitized, specified stereochemistry recorded, implicit hydrogens added, conformers generated with RDKit ETKDGv3, then minimized with MMFF94s when fully parameterized or UFF otherwise. A UFF result is explicitly warned as a different-coverage/lower-confidence fallback. The response contains atom and bond records, formal charges, stereochemistry labels, canonical isomeric SMILES, formula, and an RDKit 2D SVG; Three.js renders the returned graph rather than regenerating its connectivity.

The Advanced JSON editor now also accepts a general `{ "atoms": [...], "bonds": [...] }` molecular graph and submits it to the same validation/geometry path. Its older parser-specific JSON schemas remain supported. Graph input may encode isotope, charge, radicals, explicit hydrogens, aromaticity, tetrahedral tags, bond order, and supported E/Z bond stereo. It is not a coordination-chemistry format. In Production browser verification, a phosphoric-acid graph completed through this route, reported 0 carbon, 3 hydrogen, 5 other atoms, and 7 bonds (including generated hydrogen bonds), and appeared in the Three.js canvas with orange phosphorus.

Current explicit computational limits are 150 heavy atoms, 20 requested conformers, a 1 MB request body, and a 500-iteration force-field optimization per conformer. These are endpoint/resource bounds, not a guarantee that every molecule below the atom limit is embeddable or parameterized. A 150-carbon flexible chain is a valid graph but fails the present ETKDGv3 embedding attempt; 50 carbons succeeded. Random-coordinate retries recovered 75- and 100-carbon chains in local experiments but took longer and did not recover 150 carbons, so no unbounded retry was added. The endpoint now reports such geometry/model limits as `unsupported_geometry` / `unsupported-geometry`, rather than calling a sanitized valid structure an `invalid_structure`. A 151-heavy-atom structure is rejected before conformer generation. Twenty conformers succeeded locally for a phosphorus-containing test compound.

Disconnected species are not positioned as ion pairs or crystal structures. Spin multiplicity is checked for basic consistency but is not used to parameterize the force field. ETKDG plus MMFF94s/UFF is a conformer estimate, not quantum chemistry or an experimental structure. UFF fallback does not guarantee chemically reliable energetics for every unusual element or charge state. No support is claimed for arbitrary coordination complexes, organometallic bonding, solids, or every element/valence allowed by RDKit.

## Fixes and remaining verification

- Added regression coverage for the supplied neutral triphosphate identity and stereochemistry through IUPAC, SMILES, Molfile, and graph inputs.
- Distinguished unsupported geometry/model cases from invalid molecular structures at the API boundary.
- Added common organoboron, silicon, phosphorus, selenium, arsenic, germanium, tin, tellurium, and selected ion colors/radii; retain backend atomic numbers in rendered meshes.
- Routed generic Advanced JSON molecular graphs through the shared geometry API while keeping legacy parser JSON input.
- The exact IUPAC molecule and a phosphoric-acid Advanced JSON graph were both visually verified in the Production browser after deployment; phosphorus was orange in both renderings.
- **Still pending:** a large-molecule frontend stress test and a browser-level check of legacy parser-specific Advanced JSON. These are not inferred from the API response or local regression suite.
