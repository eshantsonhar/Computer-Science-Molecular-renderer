# AtomView Molecular Renderer

AtomView is a browser-based molecular editor and visualization website. The canonical application is [`atomview_main.html`](./atomview_main.html); [`index.html`](./index.html) redirects there.

## Molecular geometry

All active 3D molecular renderers request coordinates from the repository's Vercel Python Function at `/api/geometry`. The function uses RDKit to interpret molecular connectivity, generate ETKDGv3 conformers, and minimize them with MMFF94s or UFF when MMFF parameters are unavailable. A generated force-field conformer is a model, not an experimental or quantum-chemical structure.

- Enter structures as SMILES or an MDL Molfile, or build a graph in the embedded editor.
- The straight-chain and aromatic name parsers still cover only their implemented name subsets; they are not general IUPAC name-to-structure translators.
- The periodic-table pages generate 3D conformers only for a small, curated set of discrete species. Ionic solids, crystals, coordination compounds, and unvalidated structures display an explicit explanation instead of fabricated molecular coordinates.
- The equilibrium simulator generates and formula-checks every displayed species before enabling the simulation. Its particle motion is illustrative; the conformer geometry is not a reaction-path or thermodynamic prediction.
- The skeletal editor is a 2D topology/depicter interface. Its drawing coordinates are not treated as physical 3D coordinates.
- Older standalone renderer URLs redirect to the canonical renderer.

See [`CHEMISTRY_METHOD.md`](./CHEMISTRY_METHOD.md) for the model, validation coverage, measured angles, and limitations.

## Vercel deployment

Deploy the repository root as a Vercel project. Vercel's Python Functions support discovers `api/geometry.py`; [`requirements.txt`](./requirements.txt) pins RDKit and [`.python-version`](./.python-version) selects Python 3.12. The browser and geometry function must be deployed together because the active pages call the same-origin `/api/geometry` endpoint.

For local development, install the Vercel CLI and run:

```text
vercel dev
```

Install the Python dependencies for local geometry tests:

```text
py -3.12 -m pip install -r requirements.txt
py -3.12 -m unittest discover -s tests -v
node tests/test_parsers.js
```

The legacy Node/C++ parser server is not required for molecular geometry generation.

## Project structure

- `atomview_main.html` — primary molecular renderer and input UI.
- `api/geometry.py` — RDKit parsing, 3D conformer generation, minimization, and geometry API.
- `geometry-client.js` — shared browser client for the geometry endpoint.
- `molecule_editor.html` — embedded 2D topology editor.
- `pages/equilibrium_simulator_3d.html` — reaction-equilibrium visualization using computed conformers.
- `pages/element_template.html` and `generate_element_pages.js` — shared periodic-element renderer and page generator.
- `tests/` — parser and molecular-geometry regression tests.
