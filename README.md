# AtomView Molecular Renderer

AtomView is a browser-based molecular editor and visualization website. The canonical application is [`atomview_main.html`](./atomview_main.html); [`index.html`](./index.html) redirects there.

## Molecular geometry

All active 3D molecular renderers request coordinates from the repository's Vercel Python Function at `/api/geometry`. The function uses RDKit to interpret molecular connectivity, generate ETKDGv3 conformers, and minimize them with MMFF94s or UFF when MMFF parameters are unavailable. A generated force-field conformer is a model, not an experimental or quantum-chemical structure.

- The main renderer has one input field and a format dropdown for IUPAC names, SMILES, or MDL Molfiles. Names are interpreted by the locally bundled OPSIN 2.9.0 parser, then passed as SMILES to RDKit for geometry generation. No external chemistry API is called.
- The embedded editor can also submit a molecular graph to the same geometry endpoint.
- The periodic-table pages generate 3D conformers only for a small, curated set of discrete species. Ionic solids, crystals, coordination compounds, and unvalidated structures display an explicit explanation instead of fabricated molecular coordinates.
- The equilibrium simulator generates and formula-checks every displayed species before enabling the simulation. Its particle motion is illustrative; the conformer geometry is not a reaction-path or thermodynamic prediction.
- The skeletal editor is a 2D topology/depicter interface. Its drawing coordinates are not treated as physical 3D coordinates.
- The Organic Reactions section uses `/api/reaction_planner` for a bounded, local forward search and renders black-and-white 2D reaction schemes from molecular graphs. Its twelve curated rules cover constrained acyl substitutions, acid-chloride formation, ester saponification/acidification, catalytic hydrogenation, reductive ozonolysis, and peroxide-promoted HBr addition. The catalogue distinguishes stoichiometric reagents from catalysts/conditions; manual mode applies finite user-authorized quantities, while Auto searches the locally represented catalogue without verifying physical stock. This is not a general synthesis predictor. Drawn structures are validated and named locally with Orthonym when its verified nomenclature tier and an OPSIN round trip confirm molecular identity; unsupported names are explicitly reported as unavailable. Reaction-rule scope, textbook page references, limitations, and source-study coverage are documented in [`docs/ORGANIC_REACTIONS_EVIDENCE.md`](./docs/ORGANIC_REACTIONS_EVIDENCE.md) and [`docs/ORGANIC_REACTIONS_CHEMISTRY_STUDY.md`](./docs/ORGANIC_REACTIONS_CHEMISTRY_STUDY.md).
- Older standalone renderer URLs redirect to the canonical renderer.

See [`CHEMISTRY_METHOD.md`](./CHEMISTRY_METHOD.md) for the model, validation coverage, measured angles, and limitations.

## Vercel deployment

Deploy the repository root as a Vercel project. [`vercel.json`](./vercel.json) runs `npm run build` and serves the site's HTML and browser assets from the generated `public/` directory. The Linux build downloads and checksum-verifies a pinned Temurin 21 runtime, the Debian X11 libraries required by RDKit's Cairo-linked SVG module, and OPSIN and Orthonym's centres JAR resources. Vercel's Python 3.12 builder installs the exact NumPy, RDKit, Orthonym, lxml, JPype, and packaging versions pinned in [`requirements.txt`](./requirements.txt); the function uses those installed dependencies directly instead of duplicating them in a second wheel archive. Geometry and reaction planning share the single `api/geometry.py` Python function and its RDKit dependency bundle; a Vercel rewrite preserves the public `/api/reaction_planner` URL. The function includes only its Python modules and Java naming resources. The Java runtime and naming resources are invoked locally at request time; no runtime network access is needed. RDKit SVG depiction uses its vector drawer. The [`.python-version`](./.python-version) file selects Python 3.12. Both same-origin endpoints remain available to the browser.

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
- `chemistry/reaction_catalog.py` — locally available reagent metadata, twelve constrained reaction rules, evidence references, conditions, and limitations.
- `chemistry/reaction_planner.py` — bounded best-first search, substrate matchers, reaction graph executors, finite stoichiometric inventory, atom provenance, and independent balance validation.
- `api/vendor/opsin/` — pinned OPSIN source, parsing resources, license, local bridge, and core JAR.
- `scripts/prepare-vercel-runtime.js` — verifies OPSIN and provisions the pinned Vercel Java runtime.
- `geometry-client.js` — shared browser client for the geometry endpoint.
- `molecule_editor.html` — embedded 2D topology editor.
- `pages/equilibrium_simulator_3d.html` — reaction-equilibrium visualization using computed conformers.
- `pages/organic_reactions.html` — Organic Reactions compound entry, editor integration, inventory, route results, evidence limits, and 3D inspection.
- `docs/ORGANIC_REACTIONS_EVIDENCE.md` — reaction-rule evidence, exclusions, atom accounting, and research gaps.
- `docs/ORGANIC_REACTIONS_CHEMISTRY_STUDY.md` — textbook coverage record, chemical implications, implemented scope, and study limitations.
- `docs/TEXTBOOK_STUDY_LEDGER.md` and `docs/textbook-page-ledger.csv` — page-level study progress and explicit visual-review status for both supplied textbooks.
- `docs/ORGANIC_REACTIONS_PRODUCTION_TEST_CORPUS.csv` — production reaction, multistep, unsupported-chemistry, and browser validation cases.
- `pages/element_template.html` and `generate_element_pages.js` — shared periodic-element renderer and page generator.
- `tests/` — parser, molecular-geometry, and bounded reaction-planner regression tests.
