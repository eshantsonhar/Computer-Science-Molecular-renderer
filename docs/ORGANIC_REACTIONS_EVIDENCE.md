# Organic Reactions: evidence, scope, and implementation limits

## Evidence classification and research boundary

The primary chemistry basis for the current subset is the supplied Clayden (2nd ed.) and Bruice (7th ed.) textbooks. Reaction-level citations below identify physical PDF pages and printed pagination. The detailed document coverage and study limitations are recorded in [ORGANIC_REACTIONS_CHEMISTRY_STUDY.md](./ORGANIC_REACTIONS_CHEMISTRY_STUDY.md).

The textbooks establish qualitative mechanisms and teaching-level scope, not universal substrate compatibility, isolated yields, or experimental procedures for every accepted structure. Rules are therefore marked as constrained textbook-supported mechanisms, require explicit local substrate matchers, and retain limitations. A balanced, sanitized graph transformation is still not experimental validation. No yield, rate, equilibrium, or success probability is inferred.

## Implemented transformations

| Rule ID | Transformation | Evidence basis (PDF pages) |
|---|---|---|
| `acyl-chloride-ammonolysis` | Acyl chloride + two ammonia equivalents -> amide + ammonium chloride | Bruice pp. 778-780; Clayden pp. 232-234 |
| `acyl-chloride-aminolysis` | Acyl chloride + two equivalents of one supported primary/secondary amine -> amide + ammonium chloride | Bruice pp. 778-780; Clayden pp. 232-234 |
| `acyl-chloride-alcoholysis` | Acyl chloride + one supported alcohol -> ester + HCl | Bruice pp. 778-780; Clayden pp. 232-234 |
| `acyl-chloride-hydrolysis` | Acyl chloride + water -> carboxylic acid + HCl | Bruice pp. 778-780; Clayden pp. 232-234 |
| `acyl-chloride-anhydride-formation` | Acyl chloride + carboxylate -> anhydride + chloride | Bruice pp. 778-780; Clayden pp. 232-234 |
| `acid-chloride-formation` | Carboxylic acid + thionyl chloride -> acyl chloride + SO2 + HCl | Bruice pp. 812-813; Clayden pp. 241-242 |
| `fischer-esterification` | Saturated aliphatic carboxylic acid + primary/secondary alcohol ⇌ ester + water, under acid catalysis | [Organic Chemistry Portal: Fischer esterification](https://www.organic-chemistry.org/namedreactions/fischer-esterification.shtm) |
| `ester-saponification` | Primary alkyl ester + NaOH -> carboxylate salt + alcohol | Bruice pp. 787-788 |
| `carboxylate-acidification` | Carboxylate + HCl -> carboxylic acid + chloride | Bruice pp. 787-788 |
| `alkene-hydrogenation` | One isolated C=C + H2 -> alkane | Bruice pp. 307-309 |
| `alkyne-hydrogenation` | One isolated C≡C + two H2 -> alkane | Bruice pp. 339-369; hydrogenation context pp. 307-309 |
| `reductive-alkene-ozonolysis` | One hydrocarbon C=C + ozone/DMS -> carbonyl fragments + DMSO | Bruice pp. 303-305 |
| `peroxide-hbr-addition` | Unbranched terminal alkene + HBr -> terminal bromoalkane | Bruice pp. 610-612 |
| `primary-alcohol-to-aldehyde`, `primary-alcohol-to-carboxylic-acid`, `secondary-alcohol-to-ketone` | Narrowly scoped alcohol oxidations with distinct aldehyde, acid, and ketone outcomes | Bruice alcohol-oxidation material; exact page range not verified |
| `aldehyde-to-carboxylic-acid` | Aqueous peroxide oxidation of a simple aldehyde | Bruice aldehyde-oxidation material; exact page range not verified |
| `aldehyde-hydrogenation` | Simple aldehyde reduction to a primary alcohol | Bruice aldehyde-reduction material; exact page range not verified |
| `benzene-nitration` | Nitration of unsubstituted benzene only | Bruice, Chapter 19; exact page range not verified |
| `benzene-friedel-crafts-acylation` | Benzene acetylation with acetyl chloride/AlCl3 | [Organic Chemistry Portal: Friedel-Crafts acylation](https://www.organic-chemistry.org/namedreactions/friedel-crafts-acylation.shtm) |
| `benzene-friedel-crafts-ethylation` | Benzene ethylation with chloroethane/AlCl3 | [Organic Chemistry Portal: Friedel-Crafts alkylation](https://www.organic-chemistry.org/namedreactions/friedel-crafts-alkylation.shtm) |
| `phenolic-o-acetylation`, `aniline-n-acetylation` | Narrowly scoped O- or N-selective acetic-anhydride reactions | Bruice acyl-substitution material, pp. 778-780; these rule-specific selectivity assumptions are limited to the matched substrate patterns |
| `phenol-deprotonation` | Simple phenol -> phenoxide activation | Bruice phenol acid-base material; exact page range not verified |
| `kolbe-schmitt-carboxylation` | Simple phenoxide + CO2 -> salicylate at equivalent ortho sites | [Organic Chemistry Portal: Kolbe-Schmitt reaction](https://www.organic-chemistry.org/namedreactions/kolbe-schmitt-reaction.shtm) |
| `strecker-imine-formation`, `strecker-cyanide-addition`, `aminonitrile-hydrolysis` | Constrained aldehyde/ammonia/HCN sequence to an alpha-aminonitrile and then a carboxylate | [Organic Chemistry Portal: Strecker synthesis](https://www.organic-chemistry.org/namedreactions/strecker-synthesis.shtm) |
| `paal-knorr-pyrrole-synthesis` | Butane-1,4-dial + ammonia -> pyrrole | [Organic Chemistry Portal: Paal-Knorr pyrrole synthesis](https://www.organic-chemistry.org/namedreactions/paal-knorr-pyrrole-synthesis.shtm) |

The Phase 2 rule descriptions preserve narrow substrate gates and reaction-specific conditions in the catalogue. Several textbook citations intentionally say that the exact page range has not been verified; bibliographic pointers should not be mistaken for an exhaustive substrate-scope study. The Phase 2 browser outcomes and limitations are recorded in [`ORGANIC_REACTIONS_PHASE2_RESULTS.md`](./ORGANIC_REACTIONS_PHASE2_RESULTS.md).

Important mechanistic distinctions are preserved. Acyl substitution uses nucleophilic addition/elimination and accounts for proton transfer and expelled chloride. Fischer esterification is reversible and reports water explicitly; the planner does not estimate equilibrium position or model water removal/excess alcohol. Hydroxide saponification ends at carboxylate; neutral acid formation needs a separate acidification step. Catalytic hydrogenation, ozone cleavage with reductive work-up, and peroxide-chain HBr addition are separate rules, not generic multiple-bond edits. The peroxide effect is not extended to HCl or HI.

Substrate restrictions are encoded in `chemistry/reaction_planner.py` matchers and repeated in each catalog rule's `limitations`. For example, hydrogenation accepts only unbranched acyclic hydrocarbons with one non-aromatic multiple bond; ozonolysis accepts only a hydrocarbon with one C=C; supported amines and alcohols must have a single simple reactive site. Unsupported substrates are rejected rather than routed through an unqualified template.

## Atom, provenance, and balance model

Reaction executors construct products from explicit-hydrogen graphs of actual starting materials and reagents. Product sanitization, atom/isotope/provenance conservation, and total formal-charge conservation are checked. An independent final balance compares elemental/isotopic counts and charge for the step. Stoichiometric atom donors are separated from non-stoichiometric catalysts and initiators; catalytic Pd/C and the peroxide initiator are conditions, not net atom sources. All generated products, including coproducts and counterions, remain in the step scheme.

Atom origins refer to original starting-material or stoichiometric-reagent component IDs and canonical graph atom indices; hydrogen origins identify parent atoms and per-parent ordinals. These labels now propagate through every generated intermediate instead of relabelling intermediate atoms as new starting materials. They do not refer to screen coordinates or original Molfile indices. A product depiction is generated from that product graph; it is not guessed from a name or drawing appearance.

## Search and reporting semantics

Search is a bounded best-first forward search over user-supplied material units and reagent authorization. Limits are 20 steps, 1,000 expanded states, and 20 total starting-material units. Manual mode consumes only authorized finite reagent quantities; Auto mode can use any reagent represented by a rule but cannot verify that the user physically has it. Routes are ranked lexicographically by reaction count, stoichiometric reagent equivalents, number of explicitly listed conditions, then rule IDs. This is not a global synthesis optimum and does not rank yields, costs, evidence quality, safety, or operational convenience.

`no-supported-route` means only that the bounded search found no route in the represented subset and selected mode; it does not mean that no chemical route exists. Search-limit exhaustion is a distinct status and does not imply route absence.

## Entry names, catalogue, and interface

OPSIN is used for name-to-structure parsing and reverse verification, not as a structure-to-name engine. Structure naming uses locally installed Orthonym 1.1.0 with pinned OPSIN 2.9.0 and centres 1.2.1 JARs. The build downloads and checksums these resources and the Orthonym runtime wheels; request-time naming does not access the network. A generated PIN or systematic name is marked verified only when both Orthonym's provenance is verified and a second local OPSIN parse has the same canonical isomeric SMILES as the original validated graph. Best-effort candidates retain their tier and are explicitly marked unverified. Unsupported or mismatched compound entries say `IUPAC name unavailable for this structure`; reaction schemes use the molecular formula as a concise label when no name is available and expose that limitation in the label's accessible description. Names directly entered by the user are retained as input labels, not asserted to be generated Preferred IUPAC Names.

Every geometry response includes an RDKit-generated 2D SVG computed from the same sanitized molecular graph as the formula, canonical isomeric SMILES, and 3D conformer. Starting materials, targets, reactants, and products render those exact SVG depictions; the browser no longer approximates their structures from SMILES. The 3D inspector is hidden by default and is opened by its checkbox or an `Inspect 3D` action. Neither the 2D depiction nor the generated 3D conformer establishes reaction feasibility or experimental geometry.

## Deployment and runtime verification

The production host was rechecked on 2026-11-10. GitHub records successful Production deployments for commits `3157f32` and `7a385f6`; the latest deployment record points to `7a385f6`, and the live alias serves the matching twelve-rule catalog and redesigned workspace. `GET /api/reaction_planner` returned HTTP 200 with all twelve listed rule IDs. `POST /api/geometry` for ethanol returned HTTP 200 with canonical SMILES `CCO`, a 2D depiction SVG, and Orthonym 1.1.0 `naming.verified: true`. The live page loaded the local reagent catalogue and the new synthesis workspace. This verifies the pushed source reached production; the exact deployed Python minor version, dependency inventory, and runtime logs were not independently queried during this audit.

The production endpoint campaign and exact case inputs/results are recorded in [`ORGANIC_REACTIONS_PRODUCTION_TEST_CORPUS.csv`](./ORGANIC_REACTIONS_PRODUCTION_TEST_CORPUS.csv). Every one of the twelve catalog rules returned a route for at least one in-scope substrate. Additional tests varied carbonyl substitution, chain length, aromaticity, branching, multiple-product cleavage, and manual/automatic reagent authorization. Each returned route exposed atom-balance, charge-balance, and provenance checks as passed. Independently prepared expected molecular graphs were canonicalized and formula-checked with local RDKit; this is graph verification, not experimental validation. The separately dated [`ORGANIC_REACTIONS_CHALLENGE_AUDIT_2026-11-12.md`](./ORGANIC_REACTIONS_CHALLENGE_AUDIT_2026-11-12.md) records the exact requested name-input campaign and production-browser results.

The production browser was operated at the live URL. Direct IUPAC entry resolved propanoic acid, propan-1-ol, and propyl propanoate with verified names and separate 2D depictions. Auto mode produced and displayed the two-step acid-chloride route. A separate four-step ethyl-benzoate-to-benzamide API route and two-step ester hydrolysis/acidification route were checked step-by-step. The browser also accepted acetyl chloride as SMILES, ethanol from a V2000 Molfile, and a drawn C-C graph that was transferred as ethane (`CC`; `C2H6`). Selecting a compound opened the 3D inspector; it was hidden on a fresh page load. At viewport widths 375, 724, and 1,280 CSS pixels, the document had no horizontal overflow. No browser console errors were observed in the exercised entry paths.

Live testing also found that the checkbox labelled “Show mechanisms” revealed only explanatory prose. The label was changed to “Show reaction explanations,” covered by a UI regression test, pushed in commit `dc45ebb112a3321565729bd507427b001b9eb63a`, and verified in successful Production deployment `7687403492`. On a freshly loaded production page, the checkbox had the corrected label; after calculating the two-step propanoic-acid/propan-1-ol route, checking it displayed both reaction explanations and unchecking it hid them.

Negative production cases distinguished malformed SMILES (`invalid_structure`), unsupported internal-alkene regioselectivity and aromatic bromination (`unsupported_chemistry`), and a manual search lacking required reagent authorization (no route). A supplied ethane target returned a zero-step identity route. A carbon-free ion is rejected as a final organic target; this is an input-domain validation, not a failed chemical prediction. These checks cover representative pathways, not every UI control, structure class, or substrate in the PDFs.

An earlier production failure is documented from its actual runtime traceback: an older planner function imported RDKit without that dependency installed, causing `ModuleNotFoundError: No module named 'rdkit'`. Production probes and successful deployments for the later commits show that this is not the current endpoint behavior. Earlier Vercel build attempts exposed oversized function bundles; the current deployment success and live responses establish that these commits deployed, but do not replace a current build-log/runtime inspection.

The production site was rechecked on 2026-11-12 after commit `0df95e4`. The live catalog endpoint returned HTTP 200 with 13 rules. Browser-driven exact-name tests confirmed Auto ethene hydrogenation, the new one-step Fischer esterification, the four-step ethyl-benzoate-to-benzamide route, and a zero-step stereochemical cholesterol identity. Each inspected route matched its requested target graph; all reported per-step balance and provenance checks passed. Unsupported chemistry returned HTTP 422 without leaving stale route cards, while exact `paclitaxel` and `vancomycin` target entries were classified as `name_parse_failed` before route search. At nominal widths 375, 724, and 1280 CSS pixels, the route workspace had no horizontal overflow; the inspector was collapsed by default, the explanation checkbox toggled its text, and reagent search found sulfuric acid. See the dated challenge report for every test input and outcome. This live verification does not imply experimental feasibility or coverage beyond the bounded catalog.

Local regression checks previously recorded for this source include 46 Python tests, geometry-client and Organic Reactions UI checks, and `npm run build`. The development environment uses Python 3.11 and does not have Orthonym installed; local tests exercise fallback naming. The live production name-generation check succeeded, but the deployed Python runtime version was not independently read.

RDKit sanitization establishes graph validity, not reaction feasibility. The constrained rules and qualitative condition gates do not model kinetics, thermodynamics, yields, conversion, side reactions, safety, experimental execution, or competition from unrepresented chemistry. Force-field geometry is only a conformer model and is not reaction evidence.

## Not investigated or implemented

The catalog does not implement general alkene/alkyne chemistry beyond its narrowly scoped hydrogenation, reductive ozonolysis, and peroxide-promoted HBr addition rules. Alcohol oxidation and aldehyde reduction are limited to the specific rules above; general ketone reduction, carbonyl additions, broad acid activation, general substitution/elimination, substituted-arene regioselectivity, general C-C coupling, protection/deprotection, and organometallic chemistry remain unsupported. These families require independent evidence review, scoped templates, selectivity handling, atom accounting, and negative tests before acceptance.
