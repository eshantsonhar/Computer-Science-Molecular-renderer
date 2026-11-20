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
