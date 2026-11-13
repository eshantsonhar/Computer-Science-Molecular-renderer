# Organic Reactions assignment audit

**Audit date:** 2026-11-12
**Project tree:** `Computer-Science-Molecular-renderer` under the supplied workspace
**Purpose:** Record the first-party documentation review, verified baseline, material code/document discrepancies, and outstanding assignment requirements. This is an audit record, not a completion claim.

## Documentation inventory

All documents listed below were read in full. Vendored OPSIN and Orthonym notices were read to establish runtime and licensing boundaries. The generated/vendor OPSIN parsing corpus, `node_modules`, compiled binaries, and third-party generated resources were not treated as AtomView documentation.

| File | Subject | Read completely | Requirements and findings |
|---|---|---:|---|
| `README.md` | Product, local setup, endpoints, project map | Yes | At initial inventory time this described the 29-rule catalogue. The 2026-11-13 follow-up below records the current 39-rule catalogue and its newer scoped routes. |
| `CHEMISTRY_METHOD.md` | Geometry/naming method and reaction-planning claims | Yes | Its reaction section incorrectly said 12 rules and omitted Phase 2 families. Corrected in this audit to describe 29 rules and the linear-route limitation. |
| `docs/ORGANIC_REACTIONS_EVIDENCE.md` | Rule list, evidence, limits, atom bookkeeping, deployment history | Yes | Documents constrained scopes and correctly says graph validity is not experimental validation. Its 2026-11-10 and 2026-11-12 production counts are historical snapshots; the 2026-11-13 follow-up records current local implementation and checks. |
| `docs/ORGANIC_REACTIONS_CHEMISTRY_STUDY.md` | Textbook study and rule-design basis | Yes | Records that only 23 selected pages received visual review; the supplied textbooks were not exhaustively studied. Initial 13 rules plus 16 additions are described. |
| `docs/ORGANIC_REACTIONS_CHALLENGE_AUDIT_2026-11-12.md` | Earlier live challenge results | Yes | Historical production baseline was 13 rules with many unsupported challenges. Do not treat it as evidence of current behavior. |
| `docs/ORGANIC_REACTIONS_PHASE2_RESULTS.md` | Local 29-rule implementation and named challenges | Yes | Records all nine basic challenges, the old four-step and identity routes, and remaining advanced gaps. Its caffeine explanation attributed failure to absent chemistry but did not establish that the specified feedstocks are unsuitable; a primary-source review below corrects that interpretation. |
| `docs/ORGANIC_REACTIONS_PRODUCTION_TEST_CORPUS.csv` | Historical production positive/negative cases | Yes | Cases cover the earlier 12-rule deployment and should remain historical; they are not a 29-rule current production suite. |
| `docs/RENDERER_COMPATIBILITY.md` | Main renderer compatibility and geometry limits | Yes | Geometry failures must be reported separately from graph/name parsing; large-flexible-molecule and supported-element limits are explicit. |
| `docs/TEXTBOOK_STUDY_LEDGER.md` | Supplied-textbook page-review status | Yes | Most pages, figures, and reaction schemes have not been individually studied; extracted text alone is not marked as chemistry review. |
| `docs/test-reports/AROMATIC_PARSER_TEST_RESULTS.md` | Legacy aromatic parser test report | Yes | Reports known multiplicative-prefix and parser limitations in a separate legacy parser. The organic planner uses OPSIN/RDKit, not that parser, for its IUPAC pipeline. |
| `FEEDBACK_SETUP.md` | Feedback service setup | Yes | Unrelated to reaction planning; includes deployment configuration and security guidance. |
| `api/vendor/opsin/README.md` | Vendored OPSIN version, runtime and license | Yes | OPSIN 2.9.0 is local and MIT-licensed; no external name-resolution service is needed. |
| `api/vendor/orthonym_jars/NOTICE.md` | Structure-naming dependency licenses | Yes | Records Orthonym, OPSIN CLI, centres and shaded dependency notices. |

No `AGENTS.md` was found in the project tree. `package.json`, `requirements.txt`, and `vercel.json` were inspected as implementation/deployment configuration. The 2,657-row generated textbook ledger was inspected through its companion methodology and representative records rather than copied into this report.

## Repository and deployment baseline

The project has its own Git root and `main` branch tracking `origin/main`, at commit `641fed7` when this audit began. The parent workspace contains a separate repository with unrelated pre-existing changes; this project repository is independent. All project changes and delivery are scoped to this Git root.

The production page `https://atom-view.vercel.app/pages/organic_reactions.html` returned HTTP 200 on 2026-11-12 and again during browser testing on 2026-11-13. The initial live `GET /api/reaction_planner` returned HTTP 200, 29 rule records, and bounds of 20 steps and 1,000 expanded states. Its rule IDs matched the local 29-rule catalogue, but it had no version identifier. After version metadata was added and pushed, the live API exposed deployment identity. The latest observed Production identity on 2026-11-13 is commit `facc3293a17df900dc8e871df5eb544be6ba66a0`, build `dpl_DnEZyH4VhYwWjuRXo9uU2rYVD3js`, catalogue fingerprint `3d3662679435389f`, and 29 rules. This verifies deployment identity and catalogue parity; it does not establish experimental chemistry feasibility.

## Code architecture inspected

- `chemistry/reaction_catalog.py` contains the 29 rule records, reagent catalogue, conditions, evidence pointers, limits, and executor identifiers.
- `chemistry/reaction_planner.py` parses sanitized RDKit graphs, applies rule-specific matchers and executors, propagates source atom labels, balances all stoichiometric products, and runs a bounded best-first forward search.
- The search stores all available starting materials and intermediates in an inventory. It can choose multiple substrates for one reaction, but emits a flat ordered step list and does not expose branch/dependency edges or a convergent reaction network.
- `api/geometry.py` dispatches the geometry and reaction planner APIs. `vercel.json` rewrites `/api/reaction_planner` to the shared Python function. The browser implementation and current basic route-card rendering are in `pages/organic_reactions.html`.
- Local development has Python 3.11.9 and RDKit 2026.09.1; it does not match the deployment pin (Python 3.12 / RDKit 2026.3.5). Orthonym is not installed locally, so local structure naming uses its documented fallback behavior. No Python 3.12 interpreter is installed.

## Current production API route record

Production geometry accepted each exact IUPAC input and returned a canonical graph. Those graphs were passed to the production planner with `reagentMode: "auto"`. All target graph matches and returned balance checks passed:

| ID | Starting IUPAC names → target IUPAC name | Steps and reaction IDs |
|---|---|---|
| A1 | `ethanol` → `ethanoic acid` | 1: `primary-alcohol-to-carboxylic-acid` |
| A2 | `propan-2-ol` → `propanone` | 1: `secondary-alcohol-to-ketone` |
| A3 | `benzene` → `nitrobenzene` | 1: `benzene-nitration` |
| A4 | `2-hydroxybenzoic acid` → `2-acetyloxybenzoic acid` | 1: `phenolic-o-acetylation` |
| A5 | `4-aminophenol` → `N-(4-hydroxyphenyl)acetamide` | 1: `aniline-n-acetylation` |
| A6 | `benzene` → `1-phenylethan-1-one` | 1: `benzene-friedel-crafts-acylation` |
| A7 | `benzene` → `ethylbenzene` | 1: `benzene-friedel-crafts-ethylation` |
| A8 | `phenol` + `carbon dioxide` → `2-hydroxybenzoic acid` | 3: `phenol-deprotonation` → `kolbe-schmitt-carboxylation` → `carboxylate-acidification` |
| A9 | `benzaldehyde` → `phenylmethanol` | 1: `aldehyde-hydrogenation` |

The historical exact-name regressions also passed against the live API: ethene → ethane (1 hydrogenation step); ethanoic acid + ethanol → ethyl ethanoate (1 Fischer esterification step); cholesterol identity (0 steps); and ethyl benzoate → benzamide (4 steps: saponification → acidification → acid-chloride formation → ammonolysis). The final structures matched the requested target graphs. Per-step atom/charge balance flags passed. These are encoded graph transformations and bookkeeping checks, not experimental feasibility evidence.

Production returned structured `unsupported_chemistry` for four exact-name challenges after parsing their names: methylbenzene + benzene → N-phenylbenzamide; `1-(2-methylpropyl)benzene` → ibuprofen; 1,3-dimethylurea + cyanoacetic acid → caffeine; and ethanal + hydrogen cyanide + ammonia → `(2S)-2-aminopropanoic acid`. The caffeine result is an implementation gap: the specific feedstocks are supported in the documented Traube route (see the Phase 2 evidence correction), so the negative result does not imply feedstock unsuitability.

The current production parser also accepted the exact systematic Paclitaxel name (PubChem CID 36314, `C47H51NO14`, InChIKey `RCINICONZNJXQF-MZXODVADSA-N`) and Vancomycin name (CID 14969, `C66H75Cl2N9O24`, InChIKey `MYPYJXKWCTUITO-LYRMYLQWSA-N`). PubChem formulas and InChIKeys were re-read from its PUG REST records, then compared against the production graph with local RDKit. Both production geometry responses generated ETKDGv3/MMFF94s geometry and reported failure to converge within the 500-iteration limit. The name and graph succeeded; the bounded force-field minimization did not.

One local Python 3.11.9 / RDKit 2026.09.1 run of Auto `ethyl benzoate` → `benzamide` took 1,048 ms wall time. Search diagnostics reported 19 expanded states, 51 candidate reactions/generated states, 12 duplicate states, queue peak 21, and depth 5 reached while finding a four-step route. Python `tracemalloc` peak was 2,389,908 bytes; this excludes RDKit and other native allocations and is one measurement, not a general performance bound. The result is now emitted by the local API's search diagnostics; it is not present in the current production deployment.

## Verification performed

| Check | Result | Boundary |
|---|---|---|
| `py -3.11 -m unittest discover -s tests -v` | 62 tests passed | Uses Python 3.11 and locally installed RDKit, not pinned deployment runtime. |
| `node tests/test_parsers.js` | Passed | Legacy parser checks only. |
| `node tests/test_geometry_client.js` | Passed | Browser-client response handling checks. |
| `node tests/test_organic_reactions_ui.js` | Passed | Static/source-level UI checks; not browser automation. |
| `node tests/test_main_renderer.js` | Passed | Static renderer checks. |
| `node tests/test_element_examples.js` | Passed | Periodic-table example checks. |
| `node tests/test_crystal_renderer.js` | Passed | Crystal geometry checks. |
| `node tests/test_feedback_api.mjs` | 5 passed | One test intentionally exercises a mocked unreachable database and logs the expected fetch failure. |
| `npm run test:browser` | Passed in installed Microsoft Edge using Playwright 1.65 against Production | Exercises IUPAC entry, supported Auto route rendering, evidence details, unsupported-route handling, invalid-name rejection, exact long Paclitaxel IUPAC parsing/formula display, and 375/724/1280 px viewport widths; no console exceptions or failed requests. |
| `npm audit` | 0 vulnerabilities after refreshing vulnerable transitive packages and pinning `qs` through npm overrides | Lockfile-only dependency maintenance; production page/API behavior was separately exercised by browser checks. |
| Production page/API GET | Both HTTP 200; production reports 29 rules | Does not yet exercise an Auto route in a real browser or verify the production commit. |
| Production IUPAC-to-Auto API, A1–A9 | All 9 returned routes; final graph matched target and all reported atom/charge balance checks passed | Names were first entered into the production geometry/IUPAC endpoint; the resulting graphs were then submitted to the planner API in Auto mode. Geometry used one conformer for a faster parser/graph check. This is API testing, not browser testing. A8 returned phenoxide formation → Kolbe–Schmitt carboxylation → acidification. |
| Production historical regressions | Ethene → ethane (1 step); ethanoic acid + ethanol → ethyl ethanoate (1); cholesterol identity (0); ethyl benzoate → benzamide (4). All final graphs matched and all step balance checks passed. | Same IUPAC-to-graph plus planner API method; not browser interaction. |
| Production complex IUPAC fixtures | Exact paclitaxel and vancomycin names parsed to graphs; local RDKit InChIKeys matched the corresponding PubChem records and molecular formulas. | Both production geometry responses reported failure to converge within 500 force-field iterations. This is a geometry-optimization limit, not a name/graph failure. Reference properties were independently re-read from PubChem PUG REST on 2026-11-12. |
| Production advanced negatives | Benzanilide, ibuprofen, caffeine, and `(2S)` alanine names parsed; planner returned `unsupported_chemistry` for all four | Confirms current missing route coverage, not chemical impossibility. |
| Production version metadata | Absent at the initial probe; after the push the live GET exposes commit, build, and catalogue fingerprint | Current Production identity is recorded in the post-push deployment row below. |
| Post-push deployment | Vercel Production deployment Ready; alias reports commit `280502a4d93bc603f23e966790638c0777c8f2e3`, build `dpl_2Ma9VUYvBDAturw41SW1fB38fcJ9`, catalogue `3d3662679435389f`, and 29 rules | Live Auto `ethanol` → `ethanoic acid` returned the correct one-step rule/product graph. Live search diagnostics: 2 expanded states, 4 candidate/generated states, 0 duplicates, queue peak 3, depth 2, 3,227.875 ms. `(2S)` alanine still returns `unsupported_chemistry`. This deployment also contains the pushed browser harness and npm dependency maintenance. |
| Actual production browser interaction | Passed on 2026-11-13 with Playwright 1.65 driving installed Microsoft Edge against `https://atom-view.vercel.app/pages/organic_reactions.html` | Added IUPAC `ethanol` and `ethanoic acid` through the page, selected Auto, and rendered the one-step primary alcohol oxidation with structure depictions and opened atom-provenance/evidence details. Added `benzene` and `bromobenzene` and verified the unsupported route displays no route card and a clear status. Verified an invalid IUPAC string is rejected without an inventory entry. Added the exact long systematic Paclitaxel name and checked its `C47H51NO14` formula in the UI. Checked widths 375, 724, and 1280 px; document and body had no horizontal overflow. No uncaught page errors or failed requests. Screenshots: `browser-artifacts/production-supported-route.png` and `browser-artifacts/production-unsupported-route.png` (local ignored artifacts). |

## Material scientific correction

The Phase 2 report's explanation that caffeine feedstocks `1,3-dimethylurea` and `cyanoacetic acid` lack a documented route is too strong. Traube's original primary report is [Traube, *Berichte der Deutschen Chemischen Gesellschaft* 33 (1900), 3035–3056, DOI 10.1002/cber.19000330352](https://doi.org/10.1002/cber.19000330352). A contemporary summary states that cyanacetic acid plus urea gives cyanacetylurea ([Nature 63 (1900), 167](https://doi.org/10.1038/063167a0)); a later patent explicitly describes caffeine production from cyanoacetic acid and symmetrical dimethylurea through a pyrimidine intermediate, nitrosation, reduction to the 4,5-diaminopyrimidine, formylation/ring closure, and final N-methylation ([US2523496A](https://patents.google.com/patent/US2523496A/en)). Therefore, the feedstock choice is chemically established. The route remains unsupported by AtomView because this sequence and its necessary heterocycle transformations are not encoded, not because the starting materials are inherently inappropriate. No route is claimed as implemented or experimentally validated by this audit.

The Phase 2 report now states this distinction and cites the primary/later sources. The earlier challenge report remains a dated record of the route not being found at that time.

## Remaining assignment requirements

1. The nine Phase 2 cases and four historical regression routes have been checked against production's IUPAC/geometry and Auto planner APIs. The browser workflow has been checked for one supported and one unsupported transformation at desktop and narrow widths; the full benchmark matrix has not yet been replayed through the browser.
2. Expand browser coverage with stale-state checks and the full Phase 2/history matrix. `npm run test:browser` now provides a repeatable real-browser check using installed Edge and Playwright; repeated requests, invalid-name rejection, and long-name parsing have been exercised.
3. Implement and verify a genuine branch-and-merge route for methylbenzene + benzene to N-phenylbenzamide, including provenance and an explicit dependency/network representation in the UI.
4. Investigate and implement or precisely abstain on ibuprofen from isobutylbenzene; the current product position and regioselectivity require evidence and cannot be assumed by an aromatic graph edit.
5. Investigate and implement or precisely abstain on benzene + ethene to 2-phenylethan-1-ol with a correct two-carbon side chain and atom-source tracing.
6. Preserve the unspecified/racemic versus absolute-stereochemistry distinction in Strecker chemistry; no enantioselective or resolution route is represented.
7. Implement and validate a scoped representation of the documented Traube caffeine route. Do not describe this established feedstock pair as chemically inappropriate; no route is implemented yet.
8. Select and independently validate a literature-backed route with at least 15 distinct necessary reaction transformations. The configured 20-step bound does not demonstrate this capability.
9. Retest exact paclitaxel and vancomycin systematic names against current local code and reference structures, and separately record graph construction, 2D depiction, 3D embedding, and force-field convergence.
10. Search performance has been measured, and the code commit, Production deployment, build, catalogue identity, and two actual browser workflows are verified. Expand browser coverage as described above.
11. Chemistry/API implementation, repeatable browser harness, dependency lock/security update, and browser results are pushed to `origin/main`; deployment `dpl_2Ma9VUYvBDAturw41SW1fB38fcJ9` is Ready and its live API reports matching commit `280502a4d93bc603f23e966790638c0777c8f2e3`.

## Follow-up work — 2026-11-13

Items 3–5 above have since been implemented locally: a six-transformation convergent benzanilide route, the scoped BHC ibuprofen route with mandatory para/meta separation, and the four-step benzene + ethene route to 2-phenylethanol. The 2-phenylethanol graph, feedstock provenance, coproducts, and oxygen source are checked; the 1-phenylethanol regioisomer is a negative case. Item 10's browser matrix now covers all three routes plus prior positive and negative cases, screenshots, console/network errors, and 375/724/1280/1600 px layouts. `PYTHONPATH=tests py -3.11 -m unittest discover -s tests -v` passed 66 tests; `npm run build`, `npm audit --omit=dev`, and local Edge `npm run test:browser` passed.

The present source catalogue has 39 executable rules. Production still needs a new deployment and real-browser recheck for this source revision. Item 7 (Traube caffeine) is chemically documented and the patent route was researched, but no rule was retained because atom-mapped executors and balance/provenance tests are not yet implemented. Item 6's enantiopure `(2S)`-alanine challenge and item 8's >=15-distinct-transformation route remain open; the current search-depth setting alone does not fulfill that route requirement. Item 9's exact local and production complex-name matrix is not repeated by this follow-up. These are remaining requirements, not claims of chemical impossibility.
