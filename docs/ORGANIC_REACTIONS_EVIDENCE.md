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
| `ester-saponification` | Primary alkyl ester + NaOH -> carboxylate salt + alcohol | Bruice pp. 787-788 |
| `carboxylate-acidification` | Carboxylate + HCl -> carboxylic acid + chloride | Bruice pp. 787-788 |
| `alkene-hydrogenation` | One isolated C=C + H2 -> alkane | Bruice pp. 307-309 |
| `alkyne-hydrogenation` | One isolated C≡C + two H2 -> alkane | Bruice pp. 339-369; hydrogenation context pp. 307-309 |
| `reductive-alkene-ozonolysis` | One hydrocarbon C=C + ozone/DMS -> carbonyl fragments + DMSO | Bruice pp. 303-305 |
| `peroxide-hbr-addition` | Unbranched terminal alkene + HBr -> terminal bromoalkane | Bruice pp. 610-612 |

Important mechanistic distinctions are preserved. Acyl substitution uses nucleophilic addition/elimination and accounts for proton transfer and expelled chloride. Hydroxide saponification ends at carboxylate; neutral acid formation needs a separate acidification step. Catalytic hydrogenation, ozone cleavage with reductive work-up, and peroxide-chain HBr addition are separate rules, not generic multiple-bond edits. The peroxide effect is not extended to HCl or HI.

Substrate restrictions are encoded in `chemistry/reaction_planner.py` matchers and repeated in each catalog rule's `limitations`. For example, hydrogenation accepts only unbranched acyclic hydrocarbons with one non-aromatic multiple bond; ozonolysis accepts only a hydrocarbon with one C=C; supported amines and alcohols must have a single simple reactive site. Unsupported substrates are rejected rather than routed through an unqualified template.

## Atom, provenance, and balance model

Reaction executors construct products from explicit-hydrogen graphs of actual starting materials and reagents. Product sanitization, atom/isotope/provenance conservation, and total formal-charge conservation are checked. An independent final balance compares elemental/isotopic counts and charge for the step. Stoichiometric atom donors are separated from non-stoichiometric catalysts and initiators; catalytic Pd/C and the peroxide initiator are conditions, not net atom sources. All generated products, including coproducts and counterions, remain in the step scheme.

Atom origins refer to input component IDs and canonical graph atom indices; hydrogen origins identify parent atoms and per-parent ordinals. They do not refer to screen coordinates or original Molfile indices. A product depiction is generated from that product graph; it is not guessed from a name or drawing appearance.

## Search and reporting semantics

Search is a bounded best-first forward search over user-supplied material units and reagent authorization. Limits are 20 steps, 1,000 expanded states, and 20 total starting-material units. Manual mode consumes only authorized finite reagent quantities; Auto mode can use any reagent represented by a rule but cannot verify that the user physically has it. Routes are ranked lexicographically by reaction count, stoichiometric reagent equivalents, number of explicitly listed conditions, then rule IDs. This is not a global synthesis optimum and does not rank yields, costs, evidence quality, safety, or operational convenience.

`no-supported-route` means only that the bounded search found no route in the represented subset and selected mode; it does not mean that no chemical route exists. Search-limit exhaustion is a distinct status and does not imply route absence.

## Entry names, catalogue, and interface

OPSIN is used for name-to-structure parsing and reverse verification, not as a structure-to-name engine. Structure naming uses locally installed Orthonym 1.1.0 with pinned OPSIN 2.9.0 and centres 1.2.1 JARs. The build downloads and checksums these resources and the Orthonym runtime wheels; request-time naming does not access the network. A generated PIN or systematic name is marked verified only when both Orthonym's provenance is verified and a second local OPSIN parse has the same canonical isomeric SMILES as the original validated graph. Best-effort candidates retain their tier and are explicitly marked unverified. Unsupported or mismatched compound entries say `IUPAC name unavailable for this structure`; reaction schemes use the molecular formula as a concise label when no name is available and expose that limitation in the label's accessible description. Names directly entered by the user are retained as input labels, not asserted to be generated Preferred IUPAC Names.

Every geometry response includes an RDKit-generated 2D SVG computed from the same sanitized molecular graph as the formula, canonical isomeric SMILES, and 3D conformer. Starting materials, targets, reactants, and products render those exact SVG depictions; the browser no longer approximates their structures from SMILES. The 3D inspector is hidden by default and is opened by its checkbox or an `Inspect 3D` action. Neither the 2D depiction nor the generated 3D conformer establishes reaction feasibility or experimental geometry.

## Deployment and runtime verification

The public production host was rechecked during this continuation. `GET https://atom-view.vercel.app/api/reaction_planner` returned HTTP 200 with exactly two rules (`acetyl-chloride-ammonolysis` and `acetyl-chloride-ethanolysis`); an Auto-mode ethanoyl chloride-to-ethanamide POST returned `route-found` for the ammonolysis rule. `POST /api/geometry` for ethanol returned HTTP 200 with top-level `depictionSvg`, canonical SMILES `CCO`, and `naming.verified: true`. These probes verify the currently deployed two-rule implementation, not the twelve-rule working-tree implementation.

The production Organic Reactions HTML also remains the older version: the fetched page did not contain the new synthesis workspace or catalog loader. Thus the current UI redesign and twelve-rule catalog are not yet deployed. The public probes do not reveal the active deployment's exact commit, installed Python runtime, full dependency inventory, build size, or runtime logs. Earlier Vercel inspection notes reported Python 3.12 and a pinned Orthonym/RDKit environment for a prior deployment, but that deployment metadata was not independently rechecked in this continuation. Vercel CLI authentication is unavailable in this environment, so current runtime logs cannot be queried here.

An earlier production failure is documented from its actual runtime traceback: the old planner function imported RDKit without that dependency being installed, causing `ModuleNotFoundError: No module named 'rdkit'`. Subsequent public production probes now show its two-rule endpoint responds successfully; this does not verify that the local refactor, packaging, or expanded catalog has deployed. Prior build attempts also exposed oversized Vercel function bundles; the changed exclusions and packaging scripts still require an authenticated production build/deploy check.

Previously exercised production UI paths included direct IUPAC entry, compound SVGs, an acetyl chloride ammonolysis scheme, the on-demand 3D inspector, and a drawn C-C-O editor graph resolving to ethanol. These observations refer to prior deployments and do not verify the current redesign. Locally, the Python suite, geometry-client and Organic Reactions UI checks passed, and `npm run build` staged the pinned runtime resources. The current source was tested with Python 3.11, where Orthonym is unavailable and fallback behavior is exercised; Python 3.12 production packaging for the current source is not yet verified.

RDKit sanitization establishes graph validity, not reaction feasibility. The constrained rules and qualitative condition gates do not model kinetics, thermodynamics, yields, conversion, side reactions, safety, experimental execution, or competition from unrepresented chemistry. Force-field geometry is only a conformer model and is not reaction evidence.

## Not investigated or implemented

The catalog does not implement general alkene/alkyne chemistry beyond its narrowly scoped hydrogenation, reductive ozonolysis, and peroxide-promoted HBr addition rules. It also excludes alcohol oxidation, carbonyl additions, broad acid activation, general substitution/elimination, aromatic substitution, C-C coupling, general redox chemistry, protection/deprotection, and organometallic chemistry. These families require independent evidence review, scoped templates, selectivity handling, atom accounting, and negative tests before acceptance.
