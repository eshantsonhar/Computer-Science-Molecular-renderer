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

**Stage 7 status update:** passed against `dpl_EApc6jvNxPuasWpk3NLyPBtsuV97`, deployment URL `https://atom-view-axkkjcroo-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `e6d08a48c7edcc168789ffa9c96850e1fd85b7b9`. Edge verified exact ethanol -> ethanal plus the full regression suite.

**Stage 8 status update:** passed against `dpl_FeQi6DdCqco8QD4aroPPWqvchX6v`, deployment URL `https://atom-view-1x5r601al-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `f9cf5d51cc253c001bd5c05e7255624e6ea44f01`. Edge verified exact ethanol -> ethanoic acid and preserved the separate ethanal route.

**Stage 9 status update:** passed against `dpl_BB9YZqFe56nPpSpYVtMwEi12MCUz`, deployment URL `https://atom-view-7i5iytn3a-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `1652872c224ddf1fb982cd98e20d8aad3d9b3849`. Edge verified exact propan-2-ol -> propanone and the full regression suite.

**Stage 10 status update:** passed against `dpl_HTESsuHhg1KmGUvdFTiSgvRc33pq`, deployment URL `https://atom-view-zz1gnxcev-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `f8d2239d013671e461ddb8253a9184df00a7b3e8`. Edge verified exact benzaldehyde -> benzoic acid and the full regression suite.

**Stage 11 status update:** passed against `dpl_DUpoGoK4Dwwv67yP5xz32fcqsEZq`, deployment URL `https://atom-view-m1kxhw7zx-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `0c67fb544ab7042f35753b98e5592946cbca7e73`. Edge verified exact ethanoic acid + ethanol -> ethyl ethanoate and the full regression suite.

**Stage 12 status update:** passed against `dpl_8Sk1VUEEAofYdp95K7JNZXh6zP3V`, deployment URL `https://atom-view-7b1qihbb7-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `9ac795fd8896e62a6ff6d74e3f27ee5588b140c7`. Edge verified exact ethyl benzoate -> benzoic acid hydrolysis/saponification and the full regression suite.

**Stage 13 status update:** passed against `dpl_643LoRTjKB8SBMDQUEevESBDj7sg`, deployment URL `https://atom-view-kscl2qa9k-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `7d14f6d6106f35dbfa131fb8c72b8f140517c0e1`. Edge verified exact benzoic acid -> benzoyl chloride and the full regression suite.

**Stage 14 status update:** passed against `dpl_5qRXAk3T9pknkMdmFRCCNoUj5Wbq`, deployment URL `https://atom-view-3of22axqw-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `3a9116cd94349ab16d6be1d2962086510ac5713c`. Edge verified the four-step ethyl benzoate -> benzamide route and the full regression suite.

**Stage 15 status update:** passed against `dpl_9zywrirvjoqhs4b89bwRiAvLbno6`, deployment URL `https://atom-view-fue33m9mo-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `e9ee31b478caf9ef8ded5a2208c4805472a53f85`. Edge verified exact benzene -> nitrobenzene and the full regression suite.

**Stage 16 status update:** passed against `dpl_HVvxU6hNQcFnhgP2CQsHuoowdV4P`, deployment URL `https://atom-view-gs8ufbozx-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `d2af29f324a6a5ac06fba2e668dda6e248b1f4c6`. Edge verified exact benzene -> 1-phenylethan-1-one and the full regression suite.

**Stage 17 status update:** passed against `dpl_B66LZAKEzQ8p4jbyp8oA81b1iF6v`, deployment URL `https://atom-view-l1ri0jrv7-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `5bc7bbd75784f9722ae1b58373908de4b63d6e93`. Edge verified exact benzene -> ethylbenzene and the full regression suite.

**Stage 18 status update:** passed against `dpl_CRr5gNiY6oLyWGQcpwjrGJzbPL66`, deployment URL `https://atom-view-jeefsdpsn-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `2ef57b44b2d8ccf95f4374c8a63a81b60f23b262`. Edge verified exact phenol + carbon dioxide -> 2-hydroxybenzoic acid and the full regression suite.

**Stage 19 status update:** passed against `dpl_EQF3pyqRkuXgvtNzDDk5gG4p1pYd`, deployment URL `https://atom-view-n1v4zuj7u-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `e377ade830ef7e2fdba5c0cf796901bb0640ba46`. Edge verified exact ethanal + hydrogen cyanide + ammonia -> 2-aminopropanoic acid in four visible steps.

**Stage 20 status update:** passed against `dpl_GL1WAijyELji5jbm3kmaRtxBFgXk`, deployment URL `https://atom-view-epjj7mhbq-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `ecd87ae422c24690ccad6ab190c1339a8b56b153`. Edge verified exact butane-1,4-dial + ammonia -> 1H-pyrrole and the full regression suite.

**Stage 21 status update:** passed against `dpl_7fz9qPcexzVuvgRJwNKEegQRJnDx`, deployment URL `https://atom-view-i8lo4mqde-test09scratch2020-8996s-projects.vercel.app`, and production alias commit `458ab4feaf52f56120e217f2ea015fe61e97360e`. Edge verified exact benzene + ethene -> 2-phenylethan-1-ol in four visible steps and rejected the 1-phenylethanol isomer in the negative test.

## Stage 22: BHC ibuprofen synthesis

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Strengthened exact isobutylbenzene -> ibuprofen graph/provenance coverage.
- Asserted the ordered acetylation, para/meta separation, hydrogenation, and carbonylation sequence.
- Added a CO source assertion from the carbonylation reagent.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 53 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact isobutylbenzene -> ibuprofen with the mandatory separation and full regression matrix. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 21: Benzene-to-2-phenylethanol route

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Strengthened exact benzene + ethene -> 2-phenylethan-1-ol coverage.
- Asserted four ordered steps: ethylbenzene, styrene, styrene oxide, and primary-alcohol hydrogenolysis.
- Asserted benzene/ethene carbon provenance and peroxide-derived oxygen provenance.
- Added a wrong-isomer negative check that distinguishes 1-phenylethanol.
- Added the exact two-feedstock typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 52 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact benzene + ethene -> 2-phenylethan-1-ol in four visible steps and preserved 1-phenylethanol as a wrong-isomer negative. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 20: Paal-Knorr pyrrole synthesis

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact butane-1,4-dial + ammonia -> 1H-pyrrole graph/formula/balance coverage.
- Asserted two water coproduct molecules and nitrogen-carbon provenance.
- Added a non-C4-dial negative restriction.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 51 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact butane-1,4-dial + ammonia -> 1H-pyrrole and the full route matrix. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 19: Strecker synthesis

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Strengthened exact ethanal + hydrogen cyanide + ammonia -> unspecified alanine coverage.
- Asserted four ordered transformations: imine formation, cyanide addition, aminonitrile hydrolysis, and acidification.
- Added an explicit `(2S)` alanine unsupported/negative assertion.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 50 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact ethanal + hydrogen cyanide + ammonia -> 2-aminopropanoic acid in four visible steps. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 18: Phenoxide formation and Kolbe-Schmitt synthesis

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Strengthened exact phenol + carbon dioxide -> 2-hydroxybenzoic acid coverage.
- Asserted the route contains phenoxide formation, ortho-carboxylation, and separate acidification.
- Asserted carbon provenance includes both phenol and the CO2 feedstock.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 49 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact phenol + carbon dioxide -> 2-hydroxybenzoic acid in three visible steps. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 17: Friedel-Crafts alkylation

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact benzene -> ethylbenzene graph/formula/balance coverage.
- Added a substituted-arene negative case rejecting unmodelled regioselectivity and deactivated substrates.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 48 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact benzene → ethylbenzene and the full regression matrix. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 16: Friedel-Crafts acylation

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact benzene -> 1-phenylethan-1-one graph/formula/balance coverage.
- Added a nitrobenzene negative case rejecting extension to a deactivated substituted arene.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 47 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact benzene → 1-phenylethan-1-one and the full regression matrix. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 15: Aromatic electrophilic nitration

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact benzene -> nitrobenzene graph/formula/balance coverage.
- Added a substituted-arene negative case rejecting regioselectivity guesses.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 46 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact benzene → nitrobenzene and the full regression matrix. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 14: Amide formation and multi-step route integration

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Strengthened the exact ethyl benzoate -> benzamide route assertion for four ordered transformations.
- Verified the final benzamide graph/formula and per-step balance flags.
- Added the exact typed-name browser workflow for all four visible steps.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 45 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact ethyl benzoate → benzamide with four result steps and the final benzamide graph. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 13: Carboxylic acid activation and acid chloride formation

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact benzoic acid -> benzoyl chloride graph/formula/balance coverage.
- Asserted thionyl chloride coproducts and HCl accounting in the existing acid-chloride rule.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 44 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact benzoic acid → benzoyl chloride and the full route matrix. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 12: Ester hydrolysis and saponification

**Status:** implementation and local verification complete; deployment verification pending.

**Implementation**
- Preserved hydroxide saponification for primary esters, including aromatic ethyl benzoate.
- Added a separate acid-catalyzed hydrolysis rule for simple aliphatic primary esters.
- Kept neutral-acid formation from carboxylates as a separate acidification operation.
- Added exact ethyl-benzoate typed-name and benzamide-route regression coverage.

**Source files**
- `chemistry/reaction_catalog.py`
- `chemistry/reaction_planner.py`
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 43 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed the local ester hydrolysis and benzamide route matrix.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 11: Fischer esterification

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact ethanoic-acid + ethanol -> ethyl ethanoate graph/formula/provenance coverage.
- Asserted water is an explicit coproduct and both feedstocks contribute atoms to the ester.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 42 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact ethanoic acid + ethanol -> ethyl ethanoate and the full regression matrix. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 10: Aldehyde oxidation to carboxylic acid

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact benzaldehyde -> benzoic acid graph/formula/balance coverage.
- Added an acetone negative case preventing ketone-to-acid application of this aldehyde rule.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 41 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact benzaldehyde -> benzoic acid and the full route matrix. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 9: Secondary alcohol oxidation

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact propan-2-ol -> propanone graph/formula/ketone coverage.
- Added a primary-alcohol negative assertion.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 40 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact propan-2-ol → propanone and the full regression matrix. No console errors or failed requests.

**Git:** pending commit.

**Deployment:** pending.

**Production browser:** pending.

## Stage 8: Primary alcohol oxidation to carboxylic acid

**Status:** local implementation and browser verification complete; deployment verification pending.

**Implementation**
- Added exact ethanol -> ethanoic acid graph/formula/provenance coverage.
- Verified this strong oxidation rule remains distinct from the aldehyde-forming TEMPO rule.
- Added a phenol negative-scope assertion.
- Added the exact typed-name browser workflow.

**Source files**
- `tests/test_reaction_planner.py`
- `tests/browser_organic_reactions.mjs`
- `docs/ORGANIC_REACTIONS_27_STAGE_PROGRESS.md`

**Local tests:** 39 planner tests passed with 53 subtests.

**Local browser:** Microsoft Edge via Playwright passed exact ethanol → ethanoic acid and preserved the distinct ethanal route. No console errors or failed requests.

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
