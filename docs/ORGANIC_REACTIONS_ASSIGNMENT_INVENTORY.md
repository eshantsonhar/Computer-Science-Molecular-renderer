# Organic Reactions assignment audit

**Audit date:** 2026-11-12
**Project tree:** `Computer-Science-Molecular-renderer` under the supplied workspace
**Purpose:** Record the first-party documentation review, verified baseline, material code/document discrepancies, and outstanding assignment requirements. This is an audit record, not a completion claim.

## Documentation inventory

All documents listed below were read in full. Vendored OPSIN and Orthonym notices were read to establish runtime and licensing boundaries. The generated/vendor OPSIN parsing corpus, `node_modules`, compiled binaries, and third-party generated resources were not treated as AtomView documentation.

| File | Subject | Read completely | Requirements and findings |
|---|---|---:|---|
| `README.md` | Product, local setup, endpoints, project map | Yes | Describes the 29-rule catalogue, local OPSIN/RDKit processing, Vercel build, and existing test commands. Consistent with the current catalogue. |
| `CHEMISTRY_METHOD.md` | Geometry/naming method and reaction-planning claims | Yes | Its reaction section incorrectly said 12 rules and omitted Phase 2 families. Corrected in this audit to describe 29 rules and the linear-route limitation. |
| `docs/ORGANIC_REACTIONS_EVIDENCE.md` | Rule list, evidence, limits, atom bookkeeping, deployment history | Yes | Documents constrained scopes and correctly says graph validity is not experimental validation. Its 2026-11-10 and 2026-11-12 production counts are historical snapshots, not current identity/version metadata. |
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

The production page `https://atom-view.vercel.app/pages/organic_reactions.html` returned HTTP 200 on 2026-11-12. The initial live `GET /api/reaction_planner` returned HTTP 200, engine `AtomView curated forward synthesis search`, 29 rule records, and bounds of 20 steps and 1,000 expanded states. Its rule IDs matched the local 29-rule catalogue, but it had no version identifier. After commit `4229fe0` was pushed, Vercel reported Production deployment `dpl_7StZGcwWzyxgb1MoozNAuBvUSTge` as Ready and the live alias exposed the new fields. The live GET now reports commit `4229fe0a6a173e21dd5fecbc6bb13f054ea72776`, build `dpl_7StZGcwWzyxgb1MoozNAuBvUSTge`, and catalogue fingerprint `3d3662679435389f`, with 29 rules. This verifies deployment identity and catalogue parity. It does not establish browser interaction or experimental chemistry feasibility.

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
| Production page/API GET | Both HTTP 200; production reports 29 rules | Does not yet exercise an Auto route in a real browser or verify the production commit. |
| Production IUPAC-to-Auto API, A1–A9 | All 9 returned routes; final graph matched target and all reported atom/charge balance checks passed | Names were first entered into the production geometry/IUPAC endpoint; the resulting graphs were then submitted to the planner API in Auto mode. Geometry used one conformer for a faster parser/graph check. This is API testing, not browser testing. A8 returned phenoxide formation → Kolbe–Schmitt carboxylation → acidification. |
| Production historical regressions | Ethene → ethane (1 step); ethanoic acid + ethanol → ethyl ethanoate (1); cholesterol identity (0); ethyl benzoate → benzamide (4). All final graphs matched and all step balance checks passed. | Same IUPAC-to-graph plus planner API method; not browser interaction. |
| Production complex IUPAC fixtures | Exact paclitaxel and vancomycin names parsed to graphs; local RDKit InChIKeys matched the corresponding PubChem records and molecular formulas. | Both production geometry responses reported failure to converge within 500 force-field iterations. This is a geometry-optimization limit, not a name/graph failure. Reference properties were independently re-read from PubChem PUG REST on 2026-11-12. |
| Production advanced negatives | Benzanilide, ibuprofen, caffeine, and `(2S)` alanine names parsed; planner returned `unsupported_chemistry` for all four | Confirms current missing route coverage, not chemical impossibility. |
| Production version metadata | Absent at the initial probe; after the push the live GET exposes commit, build, and catalogue fingerprint | Current Production identity is recorded in the post-push deployment row below. |
| Post-push deployment | Vercel Production deployment Ready; alias reports commit `4229fe0a6a173e21dd5fecbc6bb13f054ea72776`, build `dpl_7StZGcwWzyxgb1MoozNAuBvUSTge`, catalogue `3d3662679435389f`, and 29 rules | Live Auto `ethanol` → `ethanoic acid` returned the correct one-step rule/product graph. Live search diagnostics: 2 expanded states, 4 candidate/generated states, 0 duplicates, queue peak 3, depth 2, 3,227.875 ms. `(2S)` alanine still returns `unsupported_chemistry`. |
| Actual production browser interaction | Not completed | Web inspection could not open the site, and Windows command execution rejected hidden Edge launch commands under its policy. Live API checks do not substitute for the requested browser workflow. |

## Material scientific correction

The Phase 2 report's explanation that caffeine feedstocks `1,3-dimethylurea` and `cyanoacetic acid` lack a documented route is too strong. Traube's original primary report is [Traube, *Berichte der Deutschen Chemischen Gesellschaft* 33 (1900), 3035–3056, DOI 10.1002/cber.19000330352](https://doi.org/10.1002/cber.19000330352). A contemporary summary states that cyanacetic acid plus urea gives cyanacetylurea ([Nature 63 (1900), 167](https://doi.org/10.1038/063167a0)); a later patent explicitly describes caffeine production from cyanoacetic acid and symmetrical dimethylurea through a pyrimidine intermediate, nitrosation, reduction to the 4,5-diaminopyrimidine, formylation/ring closure, and final N-methylation ([US2523496A](https://patents.google.com/patent/US2523496A/en)). Therefore, the feedstock choice is chemically established. The route remains unsupported by AtomView because this sequence and its necessary heterocycle transformations are not encoded, not because the starting materials are inherently inappropriate. No route is claimed as implemented or experimentally validated by this audit.

The Phase 2 report now states this distinction and cites the primary/later sources. The earlier challenge report remains a dated record of the route not being found at that time.

## Outstanding assignment requirements

1. The nine Phase 2 cases and four historical regression routes have been checked against production's IUPAC/geometry and Auto planner APIs. Their actual browser workflows have not been checked in this run.
2. Perform real browser interaction at desktop and narrow widths, including repeated requests, long structures, parser failures, and stale-state checks. Source-level DOM checks and direct API checks do not satisfy this. Attempts to access the page with the web tool failed and Windows policy rejected Edge process launch commands.
3. Implement and verify a genuine branch-and-merge route for methylbenzene + benzene to N-phenylbenzamide, including provenance and an explicit dependency/network representation in the UI.
4. Investigate and implement or precisely abstain on ibuprofen from isobutylbenzene; the current product position and regioselectivity require evidence and cannot be assumed by an aromatic graph edit.
5. Investigate and implement or precisely abstain on benzene + ethene to 2-phenylethan-1-ol with a correct two-carbon side chain and atom-source tracing.
6. Preserve the unspecified/racemic versus absolute-stereochemistry distinction in Strecker chemistry; no enantioselective or resolution route is represented.
7. Implement and validate a scoped representation of the documented Traube caffeine route. Do not describe this established feedstock pair as chemically inappropriate; no route is implemented yet.
8. Select and independently validate a literature-backed route with at least 15 distinct necessary reaction transformations. The configured 20-step bound does not demonstrate this capability.
9. Retest exact paclitaxel and vancomycin systematic names against current local code and reference structures, and separately record graph construction, 2D depiction, 3D embedding, and force-field convergence.
10. Complete the actual browser UI workflow tests. Search performance has been measured, and the code commit, Production deployment, build, and catalogue identity were verified through Vercel and the live API.
11. Code commit `4229fe0` and the audit update are pushed to `origin/main`. The current Production alias also reflects the pushed audit update and retains the same 29-rule catalogue fingerprint; the code deployment for `4229fe0` was separately verified Ready with its matching SHA.
