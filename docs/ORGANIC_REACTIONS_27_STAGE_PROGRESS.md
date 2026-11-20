# Organic Reactions 27-Stage Progress

This record contains only observed baseline facts and completed stage results. Planned stages remain unrecorded until their implementation and browser/deployment verification are complete.

## Stage 1: Chemical-name input reliability

**Status:** pass.

**Baseline**
- Repository branch: `main`
- Baseline commit: `e476a62`
- Baseline production API: 39 reaction rules
- Baseline caffeine exact-name UI inputs:
  - Starting material: `N,N'-dimethylurea`
  - Starting material: `cyanoacetic acid`
  - Target: `1,3,7-trimethyl-3,7-dihydro-1H-purine-2,6-dione`
  - Target formula parsed by production geometry: `C8H10N4O2`
  - Starting/target role counts in the successful baseline form submission: 2 starting materials and 1 target
  - Production planner status: `unsupported_chemistry`
- Root cause: the 39-rule catalogue and executor registry contain no executable caffeine Traube sequence. The displayed formic acid, nitrous acid, methyl iodide, and alkaline cyclization reagents are catalogue entries or orphan conditions, not evidence of an executable route. There is no caffeine ring-construction, nitrosation, reduction, formylation/cyclization, and final N-methylation sequence in the baseline route matchers.

**Implementation**
- Add a shared backend IUPAC-name normalizer that collapses repeated whitespace and rejects empty/multiline input.
- Normalize typed IUPAC input in the browser before sending it to `/api/geometry`.
- Preserve existing SMILES and Molfile behavior.
- Add focused geometry tests for the required Stage 1 names, repeated whitespace, empty names, and multiline names.
- Add a static UI regression asserting that typed-name submission uses the whitespace normalizer.

**Source files**
- `api/geometry.py`
- `pages/organic_reactions.html`
- `tests/test_geometry.py`
- `tests/test_organic_reactions_ui.js`

**Local tests:** `test_geometry.py` passed 31 tests and 73 subtests; reaction planner/naming regressions passed 36 tests and 50 subtests; geometry client and UI source checks passed.

**Local browser:** Microsoft Edge via Playwright passed the local typed-name matrix, including ethene, ethane, ethanol, ethanoic acid, benzene, nitrobenzene, propan-2-ol, propanone, repeated-whitespace benzene, route flows, invalid-name handling, and 375/724/1280/1600 px layouts. No console errors or failed requests. Screenshot: `browser-artifacts/local-stage1-name-inputs.png`.

**Git:** pending commit.

**Deployment:** Vercel Production deployment `dpl_jxmptaigKWRATP1oDmZRsWZVQeaV`, deployment URL `https://atom-view-1l8n8omha-test09scratch2020-8996s-projects.vercel.app`, alias `https://atom-view.vercel.app`, status `Ready`.

**Production browser:** passed in Microsoft Edge via Playwright against the production alias. Required Stage 1 names were added, repeated-whitespace benzene resolved to benzene, existing routes remained functional, invalid names remained rejected, and widths 375/724/1280/1600 had no overflow or browser failures. Production API reports commit `0b39e46b310c8b6c31939f459a2c54d0ef097992`, 39 rules, and build `dpl_jxmptaigKWRATP1oDmZRsWZVQeaV`. Caffeine baseline remains `unsupported_chemistry`.

## Stage 2: Starting-material and target separation

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Snapshot the selected starting/target role before asynchronous geometry validation, so a form edit or role change during validation cannot move the validated compound into the wrong inventory section.
- Merge duplicate compounds in the same inventory section and accumulate quantity up to the existing 20-unit limit.
- Preserve target inventory when a target is submitted; starting-material inventory remains separate.

**Source files**
- `pages/organic_reactions.html`
- `tests/test_organic_reactions_ui.js`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** UI source checks passed. Reaction planner and naming regressions passed 36 tests and 50 subtests.

**Local browser:** Microsoft Edge via Playwright passed the local Stage 2 duplicate and full route suite, including repeated-whitespace benzene merging to one starting-material card, no console errors, and no failed requests. Screenshot: `browser-artifacts/local-stage1-name-inputs.png`.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

**Stage 6 status update:** passed against `dpl_3L9pmeNK3tReKe1cYJZTFWL3qAQj`, deployment URL `https://atom-view-7hhybrl37-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `8617f6e233d9f5f81ab98e83f1f77f5d060a587b`. Edge verified benzaldehyde -> phenylmethanol and the full regression suite.

## Stage 7: Primary alcohol oxidation to aldehyde

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact ethanol -> ethanal graph/formula coverage.
- Verified the separate primary-alcohol -> carboxylic-acid rule remains distinct.
- Added phenolic and unrelated-substrate negative scope assertions.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 38 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact ethanol → ethanal, confirmed the acid route remains separate, and passed the regression matrix. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

**Stage 5 status update:** passed against `dpl_AWRVS4r4mHvi7dasJBCsjzaeb6LY`, deployment URL `https://atom-view-lskket7na-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `5c2bcb108f9301bc9462819f2ea20cf82b9253c4`. Edge verified both partial and complete alkyne hydrogenation in Auto mode.

## Stage 6: Aldehyde reduction

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact benzaldehyde -> phenylmethanol graph/formula/balance coverage.
- Added a ketone -> secondary-alcohol negative case to prove this aldehyde-only rule does not expand its substrate scope.
- Added the exact typed-name browser workflow to the permanent Edge matrix.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 37 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact benzaldehyde → phenylmethanol Auto mode and the regression matrix. No console errors or failed requests. Screenshot: `browser-artifacts/local-stage6-aldehyde-hydrogenation.png`.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

**Stage 3 status update:** passed against deployment `dpl_GvgEEbhJgLHjmxPwXgxg7NdjktCV` and production alias commit `8cfb6538978e580931b12f08119166923d076d12`. The production browser suite passed the ethanol identity route and full route regression matrix.

## Stage 4: Alkene hydrogenation

**Status:** pass.

**Implementation**
- Strengthen the exact ethene -> ethane positive regression with formula, hydrogen quantity, atom balance, charge balance, and hydrogenation rule assertions.
- Add a benzene -> cyclohexane negative case because aromatic-ring hydrogenation is outside the linear alkene rule.
- Add the exact typed-name ethene/ethane Auto browser workflow to the permanent browser matrix.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 35 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact ethene/ethane typed-name hydrogenation, plus identity and existing route regressions. No console errors or failed requests. Screenshot: `browser-artifacts/local-stage4-ethene-hydrogenation.png`.

**Git:** `d649c7b3524720cb7cd1abc515c7d0941a3469af`

**Deployment:** Vercel Production `dpl_9GSLoESqBQrgtSGYmEmHTvLPuEJ9`, URL `https://atom-view-n4scggaff-test09scratch2020-8996s-projects.vercel.app`, status `Ready`.

**Production browser:** passed in Microsoft Edge via Playwright against `https://atom-view.vercel.app`. The exact typed names ethene and ethane produced the hydrogenation route; existing identity, oxidation, Kolbe-Schmitt, convergent, ibuprofen, phenylethanol, Paclitaxel, unsupported, and responsive scenarios also passed. Screenshot: `browser-artifacts/production-stage4-ethene-hydrogenation.png`.

## Stage 5: Partial and complete alkyne hydrogenation

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added a distinct `partial-alkyne-hydrogenation` rule using Lindlar catalyst conditions and one H2 equivalent.
- Kept complete `alkyne-hydrogenation` separate, using Pd/C and two H2 equivalents.
- Changed the partial executor bond result from triple to double; complete remains triple to single.
- Added aromatic negative coverage.

**Source files**
- `chemistry/reaction_catalog.py`
- `chemistry/reaction_planner.py`
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 70 focused/geometry/name/planner tests passed with 126 subtests.

**Local browser:** Microsoft Edge via Playwright passed both `ethyne` → `ethene` and `ethyne` → `ethane`, plus the existing route suite. No console errors or failed requests. Screenshots: `browser-artifacts/local-stage5-partial-alkyne-hydrogenation.png` and `browser-artifacts/local-stage5-complete-alkyne-hydrogenation.png`.

**Git:** pending.

**Deployment:** pending.

**Production browser:** pending.
**Stage 2 status update:** passed against deployment `dpl_GibK7okYfTELVRJaEadFzqyFKDDM` and production alias commit `ce4b7b1a4c2a072818b9ff505408b720a75a98ea`. The production browser suite passed role/inventory regressions, existing routes, and 375/724/1280/1600 px layouts.

## Stage 3: Identity and zero-step routes

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Mark route responses explicitly as `identity` when the initial inventory already satisfies every target.
- Return a backend identity message and preserve a zero-length route as a valid `route-found` result.
- Display the explicit zero-step result in the typed-name UI.

**Source files**
- `chemistry/reaction_planner.py`
- `pages/organic_reactions.html`
- `tests/test_reaction_planner.py`
- `tests/test_organic_reactions_ui.js`
- `tests/browser_organic_reactions.mjs`

**Local tests:** 34 planner tests passed with 53 subtests; UI source checks passed.

**Local browser:** Microsoft Edge via Playwright passed a zero-step ethanol identity route and all existing route/regression scenarios. No console errors or failed requests. Screenshot: `browser-artifacts/local-stage3-identity-route.png`.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.
