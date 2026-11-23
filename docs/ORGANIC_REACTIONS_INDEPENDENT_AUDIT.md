# AtomView Organic Reactions — Independent Production Audit

**Date:** 23 November 2026
**Auditor:** Autonomous Junie agent (independent investigation)
**Production URL:** https://atom-view.vercel.app/pages/organic_reactions.html
**Repository:** Computer-Science-Molecular-renderer

---

## 1. Executive Summary

The AtomView Organic Reactions synthesis planner is **partially functional** — it is a narrowly scoped, evidence-based forward synthesis engine that works correctly for the reaction families it implements but is fundamentally incomplete for common undergraduate organic chemistry transformations.

**Key findings:**
- **4 of 7 tests passed** (alkene hydrogenation, primary alcohol oxidation, Fischer esterification, benzene nitration).
- **3 of 7 tests failed** (haloalkane nucleophilic substitution, haloalkane elimination, complex caffeine synthesis).
- The failures are entirely due to **missing reaction rules** — the architecture, search algorithm, and molecular graph transformations are sound for the rules that exist.
- The name-to-structure parser (OPSIN 2.9.0) works correctly for all tested chemical names.
- The backend returns HTTP 422 for unsupported chemistry, displayed as "unsupported_chemistry".
- The reaction catalog contains **35 registered reaction rules** with **~40 reagent entries**.
- The route search is a bounded best-first forward search (max 20 steps, max 1000 states).
- No deployment inconsistencies detected — local code matches production behavior.

**Classification:** The planner is a collection of well-implemented but narrowly scoped reaction exemplars. It is not fundamentally broken, but it is missing entire reaction families essential for basic organic chemistry education.

---

## 2. Production Test Results

### TEST 1 — Alkene Hydrogenation (ethene → ethane) — **PASS**
- Starting material: ethene (C2H4, SMILES: C=C)
- Target: ethane (C2H6, SMILES: CC)
- Route: 1 step — Catalytic alkene hydrogenation, Hydrogen x1, Pd/C catalyst
- Final product: ethane (C2H6) — correct
- Console: No errors. Network: HTTP 200.
- Evidence: audit-evidence/test1-ethene-to-ethane-pass.png

### TEST 2 — Primary Haloalkane Substitution (1-bromobutane → butan-1-ol) — **FAIL**
- Starting material: 1-bromobutane (C4H9Br, SMILES: CCCCBr)
- Target: butan-1-ol (C4H10O, SMILES: CCCCO)
- Result: No route found. Error: unsupported_chemistry.
- Console: HTTP 422 at /api/reaction_planner.
- Root cause: No nucleophilic substitution rules for alkyl halides in reaction catalog.
- Evidence: audit-evidence/test2-1-bromobutane-to-butan-1-ol-fail.png

### TEST 3 — Secondary Haloalkane Elimination (2-bromobutane → but-2-ene) — **FAIL**
- Starting material: 2-bromobutane (C4H9Br, SMILES: CCC(C)Br)
- Target: but-2-ene (C4H8, SMILES: CC=CC)
- Result: No route found. Error: unsupported_chemistry.
- Console: HTTP 422 at /api/reaction_planner.
- Root cause: No E2 elimination rules for haloalkanes in reaction catalog.
- Evidence: audit-evidence/test3-2-bromobutane-to-but-2-ene-fail.png

### TEST 4 — Primary Alcohol Oxidation (ethanol → ethanoic acid) — **PASS**
- Starting material: ethanol (C2H6O)
- Target: ethanoic acid/acetic acid (C2H4O2)
- Route: 1 step — Primary alcohol oxidation to carboxylic acid, H2O2 x2, Na2WO4 catalyst
- Final product: acetic acid (C2H4O2) — correct
- Console: No errors. Network: HTTP 200.
- Evidence: audit-evidence/test4-ethanol-to-ethanoic-acid-pass.png

### TEST 5 — Fischer Esterification (ethanoic acid + ethanol → ethyl ethanoate) — **PASS**
- Starting materials: ethanoic acid (C2H4O2) + ethanol (C2H6O) — two distinct materials
- Target: ethyl ethanoate/ethyl acetate (C4H8O2)
- Route: 1 step — Fischer esterification, H2SO4 catalyst
- Convergence: 2 feedstock units → 1 reaction — both starting materials contribute atoms
- Final product: ethyl acetate (C4H8O2) — correct
- Console: No errors. Network: HTTP 200.
- Evidence: audit-evidence/test5-esterification-pass.png

### TEST 6 — Benzene Nitration (benzene → nitrobenzene) — **PASS**
- Starting material: benzene (C6H6)
- Target: nitrobenzene (C6H5NO2)
- Route: 1 step — Benzene electrophilic nitration, HNO3 x1, H2SO4 catalyst
- Final product: nitrobenzene (C6H5NO2) — correct
- Console: No errors. Network: HTTP 200.
- Evidence: audit-evidence/test6-benzene-to-nitrobenzene-pass.png

### TEST 7 — Caffeine Synthesis (N,N'-dimethylurea + cyanoacetic acid → caffeine) — **FAIL**
- Starting materials: N,N'-dimethylurea (C3H8N2O) + cyanoacetic acid (C3H3NO2)
- Target: caffeine (C8H10N4O2)
- Result: No route found. Error: unsupported_chemistry.
- Console: HTTP 422 at /api/reaction_planner.
- Root cause: Traube caffeine synthesis requires ~7 transformations (condensation, nitrosation, reduction, formylation, ring closure, methylation). Reagents exist in catalog (formic acid, nitrous acid, methyl iodide) but no executable rules reference them.
- Evidence: audit-evidence/test7-caffeine-synthesis-fail.png

---

## 3. Reaction Coverage Matrix

Source: chemistry/reaction_catalog.py (RULES lines 299–1077), chemistry/reaction_planner.py (EXECUTORS lines 2924–2966)

| Reaction Family | Status | Details |
|-----------------|--------|---------|
| Alkene hydrogenation | IMPLEMENTED | alkene-hydrogenation rule, hydrogenation-alkene executor |
| Alkyne hydrogenation | IMPLEMENTED | alkyne-hydrogenation, partial-alkyne-hydrogenation |
| Alkene ozonolysis | IMPLEMENTED | reductive-alkene-ozonolysis |
| Radical HBr addition | IMPLEMENTED | peroxide-hbr-addition |
| Nucleophilic acyl substitution | IMPLEMENTED | 5 rules (ammonolysis, aminolysis, alcoholysis, hydrolysis, anhydride) |
| Acid chloride formation | IMPLEMENTED | acid-chloride-formation |
| Ester saponification | IMPLEMENTED | ester-saponification |
| Acid-catalyzed ester hydrolysis | IMPLEMENTED | acid-catalyzed-ester-hydrolysis |
| Fischer esterification | IMPLEMENTED | fischer-esterification |
| Carboxylate acidification | IMPLEMENTED | carboxylate-acidification |
| Primary alcohol → aldehyde | IMPLEMENTED | primary-alcohol-to-aldehyde |
| Primary alcohol → carboxylic acid | IMPLEMENTED | primary-alcohol-to-carboxylic-acid |
| Secondary alcohol → ketone | IMPLEMENTED | secondary-alcohol-to-ketone |
| Aldehyde → carboxylic acid | IMPLEMENTED | aldehyde-to-carboxylic-acid |
| Aldehyde hydrogenation | IMPLEMENTED | aldehyde-hydrogenation |
| Benzene nitration | IMPLEMENTED | benzene-nitration |
| Benzene Friedel-Crafts acylation | IMPLEMENTED | benzene-friedel-crafts-acylation |
| Benzene Friedel-Crafts alkylation | IMPLEMENTED | benzene-friedel-crafts-ethylation |
| Phenolic O-acetylation | IMPLEMENTED | phenolic-o-acetylation |
| Aniline N-acetylation | IMPLEMENTED | aniline-n-acetylation |
| Phenoxide formation | IMPLEMENTED | phenol-deprotonation |
| Kolbe-Schmitt carboxylation | IMPLEMENTED | kolbe-schmitt-carboxylation |
| Strecker synthesis | IMPLEMENTED | 3 rules (imine, cyanide, hydrolysis) |
| Paal-Knorr pyrrole | IMPLEMENTED | paal-knorr-pyrrole-synthesis |
| Toluene side-chain oxidation | IMPLEMENTED | toluene-side-chain-oxidation |
| Nitrobenzene hydrogenation | IMPLEMENTED | nitrobenzene-hydrogenation |
| BHC ibuprofen route | IMPLEMENTED | 3 substrate-specific rules |
| Styrene route | IMPLEMENTED | 3 substrate-specific rules |
| **Haloalkane SN1/SN2 substitution** | **NOT IMPLEMENTED** | No rules, no executors |
| **Haloalkane E1/E2 elimination** | **NOT IMPLEMENTED** | No rules, no executors |
| Aldol condensation | NOT IMPLEMENTED | No rules |
| Grignard reactions | NOT IMPLEMENTED | No rules |
| Wittig reaction | NOT IMPLEMENTED | No rules |
| Caffeine synthesis (Traube) | NOT IMPLEMENTED | Reagents exist but no rules |

**Summary:** 35 rules, ~20 executor functions, 42 executor ID mappings. Covers ~15 reaction families.

---

## 4. Architecture — Execution Flow

### Frontend (pages/organic_reactions.html, 1662 lines)
1. User enters chemical name/SMILES, selects role (starting/target), quantity.
2. resolveCandidate() POSTs to /api/geometry → OPSIN 2.9.0 converts name to SMILES.
3. Compounds stored in startingMaterials[] and targetProducts[] with canonical SMILES.
4. planRoute() POSTs to /api/reaction_planner with materials, targets, reagentMode.
5. renderResults() displays route network, steps, atom provenance, validation.

### Backend API Gateway (api/geometry.py, ~805 lines)
1. handler checks service=reaction_planner query param, delegates to chemistry.reaction_planner.handler.
2. _molecule_from_request() invokes OPSIN 2.9.0 via Java bridge for name→SMILES.
3. name_structure() in api/structure_naming.py uses Orthonym 1.1.0 for structure naming.

### Backend Reaction Planner (chemistry/reaction_planner.py, 3915 lines)
1. plan_synthesis() validates payload, parses compounds, sets up reagent inventory.
2. _search() performs bounded best-first forward search (max 20 steps, 1000 states).
3. _execute_rule() dispatches to executor functions from EXECUTORS registry.
4. _product_balance() performs independent atom/charge balance checks.
5. _route_step() assembles public output with atom provenance and bond changes.

### Reaction Catalog (chemistry/reaction_catalog.py, 1237 lines)
- RULES (line 299–1077): 35 reaction rule dictionaries.
- REAGENT_CATALOGUE (line 9–297): ~40 reagent entries.
- REFERENCES (line 1079–1236): Cited sources.

### Deployment (vercel.json, 18 lines)
- Rewrites: /api/reaction_planner → /api/geometry?service=reaction_planner
- Python serverless function, 60s max duration.
- Includes chemistry/*.py, OPSIN vendor, Orthonym jars, RDKit runtime.

---

## 5. Route-Search Algorithm Analysis

**Algorithm:** Bounded best-first forward search (chemistry/reaction_planner.py, _search() line 3506–3704).

**Parameters:**
- MAX_SEARCH_DEPTH = 20 (line 23)
- MAX_SEARCH_STATES = 1,000 (line 24)
- Priority: (reaction steps, stoichiometric reagent equivalents, conditions)

**Process:**
1. Starts with initial inventory of starting materials.
2. Min-heap priority queue ordered by (steps, reagents, conditions).
3. For each state, iterates all 35 RULES.
4. _candidate_substrate_sets() finds matching inventory molecules.
5. _execute_rule() applies the transformation on RDKit molecular graphs.
6. _product_balance() checks atom/charge balance.
7. _is_goal() compares canonical SMILES of inventory against targets.
8. _inventory_signature() deduplicates states by molecule set.
9. Stops at goal, queue exhaustion, or state limit.

**Convergent synthesis:** Supported — multiple starting materials consumed by same reaction (e.g., Fischer esterification).
**Multistep synthesis:** Supported — reactions chain through intermediates.
**Limitations:** No heuristic guidance. State deduplication by SMILES may collapse stereoisomers. 1000-state limit may be reached for complex inputs.

---

## 6. Chemical Correctness Assessment

- **Molecular Graph Transformations:** All executors operate on RDKit graphs, not string substitutions. Atom provenance tracked via _explicit_source_molecule() and _origin().
- **Atom/Charge Balance:** Independent checks via _product_balance() (line 3151). Failures raise PlannerInputError.
- **Bond Changes:** Explicitly recorded (type changes, new bonds, removed bonds).
- **Substrate Matching:** Pattern-based recognition narrowly scoped. Many rules reject molecules with additional functional groups.
- **Coproduct Handling:** Explicitly generated and tracked (water in esterification, HCl in acylation).
- **Stereochemistry:** Preserved in SMILES but search deduplicates by SMILES. 2-bromobutane test noted unspecified stereocentres.
- **Aromaticity:** Correctly handled in aromatic substitution rules.

---

## 7. Root Causes Ranked by Importance

### 1. Missing Haloalkane Substitution Rules (CRITICAL)
- **File:** chemistry/reaction_catalog.py — no SN1/SN2 rules.
- **Impact:** TEST 2 fails. Fundamental A-level reaction type.
- **Evidence:** sodium-hydroxide reagent exists (line 38) but no substitution rule uses it for alkyl halides.
- **Correction:** Add SN2 rules for primary/secondary haloalkanes with aqueous NaOH, ammonia.

### 2. Missing Haloalkane Elimination Rules (CRITICAL)
- **File:** chemistry/reaction_catalog.py — no E1/E2 rules.
- **Impact:** TEST 3 fails. Fundamental A-level reaction type.
- **Evidence:** No rule references alcoholic KOH or heat for elimination.
- **Correction:** Add E2 rules with Zaitsev/Hofmann selectivity.

### 3. Missing Caffeine Synthesis Rules (HIGH)
- **File:** chemistry/reaction_catalog.py — reagents exist (formic-acid line 269, nitrous-acid line 276, methyl-iodide line 283) but no rules reference them.
- **Impact:** TEST 7 fails.
- **Evidence:** REFERENCES cites US2523496A and US2715625A but no corresponding rules in RULES tuple.
- **Correction:** Implement full Traube pathway as 6-7 sequential rules.

### 4. Narrow Substrate Scope (MEDIUM)
- **File:** chemistry/reaction_catalog.py — limitations in individual rules.
- **Impact:** Rules may not fire for structurally similar molecules.
- **Evidence:** alkene-hydrogenation requires "linear-single-alkene" (line 490).
- **Correction:** Broaden patterns or add variant rules.

### 5. HTTP 422 for Unsupported Chemistry (LOW — by design)
- **File:** chemistry/reaction_planner.py handler.
- **Impact:** Console errors for legitimate "no route found" cases.
- **Correction:** Return HTTP 200 with structured "no route found" response.

---

## 8. Local-vs-Production Discrepancy Analysis

**No discrepancies detected.** Production matches local source code:
1. Vercel rewrite /api/reaction_planner → /api/geometry?service=reaction_planner confirmed working.
2. geometry.py serverless function includes chemistry/*.py.
3. 60s max duration sufficient for search.
4. OPSIN 2.9.0 JAR and Java runtime included.
5. All 7 test results consistent with local RULES and EXECUTORS.

---

## 9. Recommended Repair Order

### Phase 1: Foundational
1. Implement haloalkane SN2 substitution (primary, aqueous NaOH → alcohol; ammonia → amine).
2. Implement haloalkane E2 elimination (secondary/tertiary, alcoholic KOH/heat → alkene).
3. Add SN1 rules for tertiary haloalkanes.

### Phase 2: Multistep
4. Implement Traube caffeine synthesis pathway (6-7 rules).
5. Add aldol condensation rules.
6. Add Grignard reaction rules.

### Phase 3: UX
7. Change HTTP 422 to HTTP 200 for "no route found".
8. Broaden substrate scope in existing rules.
9. Add more reagent coverage (PCC, Jones, LiAlH4, NaBH4).

### Phase 4: Quality
10. Add stereochemistry handling.
11. Add regioselectivity reporting.
12. Improve error messages.

---

## 10. Limitations

### Verified
- All 7 tests executed via Playwright against live Vercel deployment.
- Complete reaction catalog (35 rules) audited from source.
- EXECUTORS registry (42 mappings) fully examined.
- Route search algorithm traced through source.
- OPSIN pipeline verified for all test inputs.
- Deployment config confirmed consistent with production.
- Console messages and network codes captured.
- Screenshots captured for all 7 tests.

### Not Verified
- Internal RDKit transformations not unit-tested independently.
- OPSIN edge cases beyond 12 test names.
- Performance under load.
- Drawing/sketching workflow (excluded per instructions).
- Caffeine pathway intermediates not verified against primary literature.

---

## Chemical References

- Bruice, Organic Chemistry, 7th ed. — hydrogenation, ozonolysis, alcohol oxidation, electrophilic aromatic substitution
- Clayden, Greeves & Warren, Organic Chemistry, 2nd ed. — acyl substitution, acid activation
- US2523496A — Traube caffeine synthesis (https://patents.google.com/patent/US2523496A/en)
- US2715625A — Cyanoacetylurea condensation (https://patents.google.com/patent/US2715625A/en)
- Organic Chemistry Portal — Fischer esterification, Friedel-Crafts, Kolbe-Schmitt, Strecker synthesis

---

## Evidence Directory

Screenshots in audit-evidence/:
- test1-ethene-to-ethane-pass.png (PASS)
- test2-1-bromobutane-to-butan-1-ol-fail.png (FAIL)
- test3-2-bromobutane-to-but-2-ene-fail.png (FAIL)
- test4-ethanol-to-ethanoic-acid-pass.png (PASS)
- test5-esterification-pass.png (PASS)
- test6-benzene-to-nitrobenzene-pass.png (PASS)
- test7-caffeine-synthesis-fail.png (FAIL)
