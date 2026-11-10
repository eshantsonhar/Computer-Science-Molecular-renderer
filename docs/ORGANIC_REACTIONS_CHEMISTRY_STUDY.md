# Organic Reactions: chemistry study and rule-design basis

## Source examination and coverage

The study used the two supplied PDFs:

1. `organic chemistry clayden 2nd edition -- Jonathan Clayden; Nick Greeves; Stuart G Warren -- 2_ ed .pdf` — 1,265 physical PDF pages.
2. `Organic Chemistry -- Paula Yurkanis Bruice -- 7.pdf` — 1,392 physical PDF pages.

Page-delimited text was extracted for every physical page, and the chapter outlines and end-of-chapter reaction summaries were inventoried. Clayden has substantive extracted text on 1,260 pages; Bruice has substantive extracted text on 1,391 pages, with its first physical page empty. Sparse-text pages were rendered for visual inspection. Reaction-summary pages and selected alkene, radical, and acyl-substitution schemes were also inspected as rendered pages.

This is not a claim that every embedded illustration in either book was visually inspected individually. Structures and arrow-pushing schemes can be linearized or lose stereochemical detail during text extraction; the inspected schemes supplement, but do not replace, a complete visual review of all figures. Important implemented rules therefore have narrow scopes and explicit abstention conditions.

The references below use **physical PDF page numbers**, not printed page numbers. For orientation, the Bruice PDF is approximately 41 pages ahead of its printed pagination in the cited chapters; Clayden is approximately 27 pages ahead in its cited chapters.

## Chemistry relevant to synthesis planning

The books treat synthesis as a connected sequence of functional-group changes, not a lookup from one named group to one universal product. A useful planner must account for the molecular graph, atom source, reagent role, conditions, and competing pathways at each step.

| Reaction area | Chemistry understood from the texts | Consequence for a computational planner |
|---|---|---|
| Alkene and alkyne chemistry | HX addition can follow carbocation chemistry, with regioselectivity and possible rearrangement; halogen addition proceeds through a bridged intermediate and differs in stereochemical outcome; hydroboration/oxidation has different regiochemistry from acid hydration; catalytic hydrogenation, partial alkyne reduction, and oxidative cleavage are distinct transformations. | Do not implement a generic “add atoms across a multiple bond” rule. Encode the reagent and mechanism, preserve or enumerate stereochemistry, and reject substrates where rearrangement or competing unsaturation is not handled. |
| Radical chemistry | Radical chains have initiation, propagation, and termination steps. The peroxide effect is specific to HBr: Br-radical addition gives anti-Markovnikov regiochemistry because it forms the more stable carbon radical. Radical and ionic HBr addition are not interchangeable. | Treat peroxide-promoted HBr addition as its own rule. Do not apply it to HCl or HI, and do not silently substitute its product for the ionic-addition product. |
| Substitution and elimination | SN2 is concerted and inverts a reacting stereocentre; SN1 proceeds through a carbocation and may racemize or rearrange. E2 requires an appropriate antiperiplanar arrangement, while E1 competes through a carbocation. Substrate, leaving group, nucleophile/base, solvent, and temperature affect competition and regio-/stereochemistry. | A connectivity-only substitution or elimination template is insufficient. Rules need explicit stereochemical constraints and a limited substrate domain; otherwise the planner must abstain. |
| Alcohols, ethers, and epoxides | Alcohol hydroxyl groups often need activation before substitution. Williamson ether synthesis is an SN2 process. Epoxide openings have different attack-site preferences under acidic and basic conditions and are stereochemically constrained. | Conditions and substrate activation affect the bond edit. Ring opening must preserve the correct geometry and distinguish acid- from base-controlled regiochemistry. |
| Carboxylic-acid derivatives | Acyl substitution proceeds by nucleophilic addition to a carbonyl followed by elimination. Leaving-group basicity and resonance make acyl chlorides much more reactive than esters and amides; amides need substantially harsher hydrolysis conditions. Acid chlorides react with water, alcohols, amines, and carboxylates, but these nucleophiles give different products. Thionyl chloride activates carboxylic acids to acid chlorides. | Keep acyl substitution separate from aldehyde/ketone addition. Account for neutral-nucleophile proton transfer, salt/coproduct formation, and the chosen derivative's reactivity. Do not infer universal conversion or conditions from a single example. |
| Aldehydes, ketones, and conjugated carbonyls | Carbonyl addition converts C=O to C-O while forming a new bond to the electrophilic carbon. Hydride and organometallic reactions have different atom donors and work-ups. Alpha,beta-unsaturated carbonyls can react at the carbonyl or by conjugate addition; imine/acetal formation and hydrolysis have distinct conditions and equilibria. | Reagent identity determines which bond is formed. Work-up, protonation, and 1,2 versus 1,4 selectivity must be represented; a valid product graph alone does not establish feasibility. |
| Enolates and carbon-carbon bond formation | Enolate generation enables alpha-substitution, aldol, Claisen/Dieckmann, Michael, and related reactions. Regioselectivity depends on substrate and kinetic versus thermodynamic control; crossed condensations can have competing products. Organometallic additions require compatibility with protic groups and a protonating work-up. | These families require richer selectivity and compatibility models than the initial planner has. They should not be added as broad templates without representing those decisions. |
| Aromatic and heterocyclic chemistry | Electrophilic aromatic substitution retains aromaticity, but substituents control ring activation and orientation. Heteroaromatic reactivity is not safely inferred from benzene rules. | A single aromatic substitution template cannot choose a unique position for arbitrary substituted rings. |
| Pericyclic and stereospecific reactions | Electrocyclic, cycloaddition, and sigmatropic reactions are concerted; orbital symmetry and thermal/photochemical conditions control allowed pathways and stereochemical outcomes. | Encode the relevant orbital-symmetry and stereochemical rule, or leave the transformation unsupported. |
| Functional-group synthesis and retrosynthesis | Bruice's synthesis appendices index routes to functional groups and carbon-carbon bonds (PDF pp. 1343-1346). Clayden's chapters and synthesis material connect transformations through intermediates and functional-group interconversions. The appendices are indexes, not proof of universal substrate scope. | Use the appendices to identify candidate families, then use the mechanism chapters to establish scope, conditions, atom provenance, and limitations before implementing a rule. |

## Evidence selected for the implemented rule family

The cited pages support qualitative mechanisms and constraints. They do not provide a universal reaction database, predicted yields, or experimental feasibility for every substrate accepted by a graph rule.

| Transformation family | Source evidence and model implication |
|---|---|
| Acyl-chloride substitution with ammonia, amines, alcohols, water, or carboxylate | Bruice, PDF pp. 778-780 (printed pp. 737-739), describes the tetrahedral-intermediate mechanism, different nucleophile/product pairs, and why two equivalents of an amine or ammonia are used. Clayden, PDF pp. 232-234 (printed pp. 205-207), compares derivative reactivity and explains the role of leaving-group ability and amide resonance. Rules must use the actual nucleophile and represent proton transfers and coproducts. |
| Carboxylic acid activation by thionyl chloride | Bruice, PDF pp. 812-813 (printed pp. 771-772), and Clayden, PDF pp. 241-242 (printed pp. 214-215), describe acid-to-acyl-chloride conversion and sulfur-containing coproducts. The net graph must account for both chlorines, both sulfur-dioxide oxygens, and the acid proton; merely replacing OH with Cl is not atom-balanced. |
| Ester hydrolysis under hydroxide | Bruice, PDF pp. 787-788 (printed pp. 746-747), explains hydroxide as a consumed nucleophile and identifies carboxylate plus alcohol as the products; this differs from reversible acid-catalyzed hydrolysis. A model must not emit a neutral acid without an explicit acid work-up. |
| Catalytic hydrogenation | Bruice, PDF pp. 307-309 (printed pp. 266-268), describes H2 addition in the presence of a metal catalyst, syn addition, and the possibility of cis/trans isomerization under hydrogenation conditions. Initial rules are limited to substrates for which full reduction has no unresolved chemoselectivity or newly created stereocentre. |
| Reductive ozonolysis | Bruice, PDF pp. 303-305 (printed pp. 262-264), explains C=C cleavage, carbonyl formation, and reductive work-up; the unstable ozonide is not treated as an isolated product. The atom-balanced net model must account for the third ozone oxygen in the sulfur-oxide work-up coproduct. |
| Peroxide-promoted HBr addition | Bruice, PDF pp. 610-612 (printed pp. 569-571), distinguishes radical addition from ionic addition, explains the anti-Markovnikov orientation from radical stability, and notes that the peroxide effect does not apply to HCl or HI. This is a separate, condition-dependent rule, not a generalized HX-addition template. |

## Rule-design decisions and deferred chemistry

Implemented transformations are restricted to cases where the planner can make the graph edit, track all stoichiometric atoms and formal charge, validate every product, and describe the relevant selectivity without inventing yields. Reaction-rule conditions, catalysts, initiators, solvents, and work-ups are distinct from stoichiometric atom donors. Catalysts/initiators are not counted as consumed atoms; each such omission is identified explicitly in the rule metadata.

The current locally executable subset contains twelve rules:

| Rule | Supported graph transformation | Important modeled boundary |
|---|---|---|
| Acyl chloride ammonolysis | Acyl chloride + two NH3 -> amide + ammonium chloride | One simple acyl chloride; one ammonia equivalent forms the amide and the second accepts the acid equivalent. |
| Acyl chloride aminolysis | Acyl chloride + two equivalents of the same primary/secondary amine -> amide + ammonium chloride | One simple amine site; aromatic, tertiary, multifunctional, and competing nucleophiles are excluded. |
| Acyl chloride alcoholysis | Acyl chloride + one simple alcohol -> ester + HCl | One unambiguous acyl chloride and primary/secondary alcohol site. |
| Acyl chloride hydrolysis | Acyl chloride + water -> carboxylic acid + HCl | Water is the explicit nucleophile and HCl is retained as a coproduct. |
| Acyl chloride anhydride formation | Acyl chloride + carboxylate -> anhydride + chloride | One unambiguous site of each type; counterions remain represented. |
| Acid chloride formation | Carboxylic acid + SOCl2 -> acyl chloride + SO2 + HCl | One simple acid and no other free O-H/N-H site. |
| Ester saponification | Primary alkyl ester + NaOH -> sodium carboxylate + alcohol | One simple ester; the result is not neutralized without a separate acidification step. |
| Carboxylate acidification | Carboxylate + HCl -> carboxylic acid + chloride | One carboxylate site; counterions and chloride are explicit. |
| Alkene hydrogenation | One isolated C=C + H2 -> alkane | Unbranched acyclic hydrocarbon only, with Pd/C explicitly required as a condition. |
| Alkyne hydrogenation | One isolated C≡C + two H2 -> alkane | Unbranched acyclic hydrocarbon only; partial reduction is not represented and Pd/C is required. |
| Reductive alkene ozonolysis | One hydrocarbon C=C + O3 + dimethyl sulfide -> carbonyl fragments + dimethyl sulfoxide | Exactly one C=C and hydrocarbon-only substrate; reductive work-up is explicit. |
| Peroxide-promoted HBr addition | Terminal alkene + HBr -> terminal bromoalkane | Unbranched terminal hydrocarbon alkene only; peroxide initiation is represented as a non-stoichiometric condition, and the rule is HBr-specific. |

These are not twelve universally applicable reaction templates. The rule metadata carries substrate matcher keys, stoichiometric reagent requirements, non-stoichiometric conditions, evidence references, mechanism text, safety notices, and limitations. The planner uses actual molecular graphs for candidate matching and graph edits; rule labels alone do not generate products. The catalog and matcher implementation are intentionally conservative and should be expanded only alongside rule-specific evidence and tests.

Search is a bounded forward best-first search over finite starting-material quantities and either finite manual reagent quantities or the unlimited *authorization* of Auto mode. A route is ranked lexicographically by reaction count, consumed stoichiometric reagent equivalents, the number of listed conditions, then rule identifiers. Manual quantities constrain consumption; Auto mode does **not** check purchasing or laboratory stock. This objective is optimal only within the encoded rules, input inventory, mode, and search bounds. It does not optimize evidence quality (the current rules share a source class), yield, cost, safety, or operational convenience. Those properties must not be inferred from the ranking.

The initial rule set does **not** claim general organic synthesis coverage. In particular, it does not yet model general SN1/SN2/E1/E2 competition, rearrangements, hydroboration/oxidation, partial alkyne reduction, organometallic additions, enolate chemistry, aromatic regioselectivity, protecting-group strategy, broad amide hydrolysis, or pericyclic stereochemistry. Those families need additional substrate-specific evidence and/or explicit models for regioselectivity, stereochemical mixtures, reagent compatibility, proton transfers, or coproducts.

For every supported step:

- The product graph is generated from identified reactant graphs rather than from a product name or drawing.
- Explicit hydrogens, heavy atoms, isotopes, formal charge, and atom origins are checked across stoichiometric reactants and products.
- The substrate matcher rejects unsupported or ambiguous reactive sites instead of selecting the first matching atom silently.
- A rule's conditions and scope are reported with textbook page references.
- A route means only that the bounded search found a sequence of supported graph transformations. It does not establish yield, kinetics, thermodynamics, scale-up safety, or experimental success.

No measured yields or probabilities are inferred from the textbooks. Experimental procedures and operational instructions are outside the planner's evidence claims.
