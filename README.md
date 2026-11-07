# AtomView Molecular Renderer

AtomView is a browser-based molecular editor and visualization website. The canonical application is [`atomview_main.html`](./atomview_main.html); [`index.html`](./index.html) redirects there.

## Molecular geometry

All active 3D molecular renderers request coordinates from the repository's Vercel Python Function at `/api/geometry`. The function uses RDKit to interpret molecular connectivity, generate ETKDGv3 conformers, and minimize them with MMFF94s or UFF when MMFF parameters are unavailable. A generated force-field conformer is a model, not an experimental or quantum-chemical structure.

- The main renderer has one input field and a format dropdown for IUPAC names, SMILES, or MDL Molfiles. Names are interpreted by the locally bundled OPSIN 2.9.0 parser, then passed as SMILES to RDKit for geometry generation. No external chemistry API is called.
- The embedded editor can also submit a molecular graph to the same geometry endpoint.
- The periodic-table pages generate 3D conformers only for a small, curated set of discrete species. Ionic solids, crystals, coordination compounds, and unvalidated structures display an explicit explanation instead of fabricated molecular coordinates.
- The equilibrium simulator generates and formula-checks every displayed species before enabling the simulation. Its particle motion is illustrative; the conformer geometry is not a reaction-path or thermodynamic prediction.
- The skeletal editor is a 2D topology/depicter interface. Its drawing coordinates are not treated as physical 3D coordinates.
- The Organic Reactions section uses `/api/reaction_planner` for a bounded, local forward search and renders black-and-white 2D reaction schemes from molecular graphs. Its evidence-backed rule set remains limited to two exact acetyl chloride examples; Auto mode selects only the ammonia required by the supported ammonolysis rule, and the searchable catalogue contains only reagents represented by those rules. It is not a general synthesis predictor. The local OPSIN integration resolves supplied names to structures but does not generate IUPAC names from drawn structures; the interface labels such structures as unnamed rather than inventing a name. Reaction evidence, source quality, exclusions, stoichiometry, coproducts, provenance checks, and scientific limitations are documented in [`docs/ORGANIC_REACTIONS_EVIDENCE.md`](./docs/ORGANIC_REACTIONS_EVIDENCE.md).
- Older standalone renderer URLs redirect to the canonical renderer.

See [`CHEMISTRY_METHOD.md`](./CHEMISTRY_METHOD.md) for the model, validation coverage, measured angles, and limitations.

## Vercel deployment

Deploy the repository root as a Vercel project. [`vercel.json`](./vercel.json) runs `npm run build` and serves the site's HTML and browser assets from the generated `public/` directory, while leaving API and chemistry-runtime files out of the static output. The build downloads and verifies a pinned Eclipse Temurin 21 Linux JDK, then links only the `java.base` and `java.xml` modules into a compact runtime archive. It also downloads and verifies pinned CPython 3.12 Linux wheels for NumPy and RDKit into a compressed archive; Pillow is omitted because the APIs do not use RDKit's image-drawing features. The geometry function includes these archives, the local OPSIN Java bridge, and the pinned OPSIN core, then extracts the runtimes to `/tmp` on first use to stay within Vercel's function bundle limit. OPSIN runs locally, without its hosted service. The reaction planner reuses the RDKit runtime and geometry parser. Vercel's Python Functions support discovers `api/geometry.py` and `api/reaction_planner.py`; [`.python-version`](./.python-version) selects Python 3.12, while [`requirements.txt`](./requirements.txt) documents the wheels provisioned by the build. The browser and both functions must be deployed together because active pages call the same-origin `/api/geometry` and `/api/reaction_planner` endpoints.

For local development, install the Vercel CLI and run:

```text
vercel dev
```

Do not use a static-only server such as `python -m http.server` to test the chemistry endpoints: it returns an HTML 404 for `/api/geometry` and `/api/reaction_planner`, because it does not execute Vercel functions. The browser client now reports the HTTP status and unexpected content type instead of trying to parse that HTML as JSON.

Install the Python dependencies for local geometry tests:

```text
py -3.12 -m pip install -r requirements.txt
```

Install Java 21 and make `java` available on `PATH` for local IUPAC parsing. The build script provisions the pinned Linux JRE on Linux builds; Windows and macOS development use Java on `PATH`. Then run:

```text
py -3.12 -m unittest discover -s tests -v
node tests/test_parsers.js
node tests/test_geometry_client.js
node tests/test_organic_reactions_ui.js
```

The legacy Node/C++ parser server is not required for molecular geometry generation.

## Project structure

- `atomview_main.html` — primary molecular renderer and input UI.
- `api/geometry.py` — RDKit parsing, 3D conformer generation, minimization, and geometry API.
- `api/reaction_planner.py` — bounded forward search, two exact reaction graph transformations, stoichiometric inventory, atom provenance, and balance validation.
- `api/vendor/opsin/` — pinned OPSIN source, parsing resources, license, local bridge, and core JAR.
- `scripts/prepare-vercel-runtime.js` — verifies OPSIN and provisions the pinned Vercel Java runtime.
- `geometry-client.js` — shared browser client for the geometry endpoint.
- `molecule_editor.html` — embedded 2D topology editor.
- `pages/equilibrium_simulator_3d.html` — reaction-equilibrium visualization using computed conformers.
- `pages/organic_reactions.html` — Organic Reactions compound entry, editor integration, inventory, route results, evidence limits, and 3D inspection.
- `docs/ORGANIC_REACTIONS_EVIDENCE.md` — reaction-rule evidence, exclusions, atom accounting, and research gaps.
- `pages/element_template.html` and `generate_element_pages.js` — shared periodic-element renderer and page generator.
- `tests/` — parser, molecular-geometry, and bounded reaction-planner regression tests.
