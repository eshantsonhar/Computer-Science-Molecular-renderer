# Organic Reactions production challenge audit

**Run date:** 2026-11-12  
**Environment:** live production UI at `https://atom-view.vercel.app/pages/organic_reactions.html`  
**Mode:** Auto for every route search. Inputs were entered through the website by their supplied names; no SMILES were substituted for failed names.

This records the requested synthesis challenge cases and UI checks. “Unsupported chemistry” means only that the deployed, curated forward-search engine found no route in its rules and configured limits; it does not establish that no experimental route exists. A parsed and sanitized graph is not proof of reaction feasibility.

## Exact-name challenge results

| Case | Starting material name(s), exactly entered | Target name, exactly entered | Input and Auto result |
|---|---|---|---|
| 1.1 | `ethanol` | `ethanoic acid` | Both names parsed; target graph `CC(=O)O`. HTTP 422 `unsupported_chemistry`; no oxidation rule or route cards. |
| 1.2 | `propan-2-ol` | `propanone` | Both names parsed; target graph `CC(C)=O`. HTTP 422 `unsupported_chemistry`; no alcohol-oxidation rule. |
| 1.3 | `benzene` | `nitrobenzene` | Both names parsed; target graph `O=[N+]([O-])c1ccccc1`. HTTP 422 `unsupported_chemistry`; aromatic nitration is not represented. |
| 1.4 | `ethene` | `ethane` | Both names parsed; HTTP 200 `route-found`, one `alkene-hydrogenation` step. Product `CC` exactly matches the target graph. Atom balance, charge balance, product sanitization, and atom provenance checks passed. |
| 1.5 | `ethanoic acid`; `ethanol` | `ethyl ethanoate` | All names parsed; HTTP 200 `route-found`, one `fischer-esterification` step. Product `CCOC(C)=O` matches the target; water is an explicit coproduct. Conditions disclose catalytic sulfuric acid, heating, and reversibility; equilibrium and conversion are not predicted. Step balance, charge, and provenance checks passed in the production response. |
| 2.1 | `2-hydroxybenzoic acid` | `2-acetyloxybenzoic acid` | Both names parsed; HTTP 422 `unsupported_chemistry`. No phenol-selective acetylation rule; no product was proposed. |
| 2.2 | `4-aminophenol` | `N-(4-hydroxyphenyl)acetamide` | Both names parsed; HTTP 422 `unsupported_chemistry`. No selective N-acetylation rule; no product was proposed. |
| 2.3 | `benzene` | `1-phenylethan-1-one` | Both names parsed; HTTP 422 `unsupported_chemistry`. Friedel–Crafts acylation is not represented. |
| 2.4 | `benzene` | `ethylbenzene` | Both names parsed; HTTP 422 `unsupported_chemistry`. Friedel–Crafts alkylation and its selectivity concerns are not represented. |
| 2.5 | `phenol`; `carbon dioxide` | `2-hydroxybenzoic acid` | All names parsed, including the carbon-free starting material; HTTP 422 `unsupported_chemistry`. Kolbe–Schmitt carboxylation is not represented. |
| 2.6 | `benzaldehyde` | `phenylmethanol` | Both names parsed; HTTP 422 `unsupported_chemistry`. Aldehyde reduction is not represented. |
| 3.1 | `1-(2-methylpropyl)benzene` | `2-[4-(2-methylpropyl)phenyl]propanoic acid` | Both names parsed; HTTP 422 `unsupported_chemistry`. The catalog lacks the required aromatic acylation, para-selective side-chain construction, and carbon-skeleton transformation sequence. |
| 3.2 | `ethanal`; `hydrogen cyanide`; `ammonia` | `(2S)-2-aminopropanoic acid` | All three starting names and the stereochemical target parsed; ammonia was accepted as a separate starting material. Target graph `C[C@H](N)C(=O)O`. HTTP 422 `unsupported_chemistry`; no Strecker route or stereochemical resolution was proposed. The planner therefore makes no claim of producing enantiopure L-alanine. |
| 3.3 | `benzene`; `ethene` | `2-phenylethan-1-ol` | All names parsed; HTTP 422 `unsupported_chemistry`. No supported aryl–carbon bond construction or side-chain-selective route. |
| 3.4 | `1,3-dimethylurea`; `cyanoacetic acid` | `1,3,7-trimethylpurine-2,6-dione` | All names parsed; HTTP 422 `unsupported_chemistry`. No purine-ring construction, regioselective N-methylation, or required heterocycle/carbonyl assembly rules; no direct conversion was invented. |
| 3.5 | `cholest-5-en-3beta-ol` | `cholest-5-en-3beta-ol` | Both entries parsed to the same stereochemical graph, `CC(C)CCC[C@@H](C)[C@H]1CC[C@H]2[C@@H]3CC=C4C[C@@H](O)CC[C@]4(C)[C@H]3CC[C@]12C`. HTTP 200 `route-found`, zero reaction steps; no stereochemistry change. The UI displayed the generated systematic name as verified. |
| 4.1 | `benzene`; `ethene`; `methanol` | `paclitaxel` | Starting materials parsed. OPSIN rejected the exact target name with `name_parse_failed`; no target graph was accepted and the planner was not invoked. This is a name-parser failure, not evidence about route-search depth or paclitaxel chemistry. |
| 4.2 | `benzene`; `ethanol`; `methanol` | `vancomycin` | Starting materials parsed. OPSIN rejected the exact target name with `name_parse_failed`; no target graph was accepted and the planner was not invoked. This is a name-parser failure, not evidence about large-graph search or vancomycin chemistry. |
| 4.3 | `ethyl benzoate` | `benzamide` | HTTP 200 `route-found`, four displayed steps: ester saponification → carboxylate acidification → acid-chloride formation → acyl-chloride ammonolysis. Final product `NC(=O)c1ccccc1` matches the entered target. Every step reported atom balance, charge balance, and complete provenance. Final atom origins traced to ethyl benzoate (13 atoms) and one ammonia equivalent (3 atoms); the second ammonia equivalent accounts for HCl capture. |
| 4.4 | `ethanal`; `hydrogen cyanide`; `ammonia` | `(2S)-2-aminopropanoic acid` | The three-feedstock L-alanine challenge was used as the complex convergent case. All feedstocks remained separate starting materials and parsed; Auto returned HTTP 422 `unsupported_chemistry`. No route was fabricated, so contributions from all three materials could not be established. This repeats case 3.2 and is not a successful multi-feedstock synthesis. |

## Multi-step route inspection

The four-step ethyl benzoate-to-benzamide route was generated in the live UI and inspected step-by-step. The target was kept in the target-product list, not added to the starting-material list. The API returned four reaction schemes and the UI displayed `Step 1` through `Step 4` in order. All four steps reported `atomBalanceChecked`, `chargeBalanceChecked`, and `atomProvenanceComplete` as true; the final canonical graph was `NC(=O)c1ccccc1`, equal to the parsed benzamide target.

The route shows explicit coproducts and stoichiometric requirements. Its displayed conditions are limited to aqueous hydroxide for saponification, stoichiometric acidification, thionyl chloride activation with SO2/HCl coproducts, and cold ammonia (two equivalents) for ammonolysis. These are rule annotations, not an experimental protocol, prediction of selectivity/yield, or proof that the full sequence is operationally optimized.

Four steps is the longest useful multi-step route verified in this campaign. This is not a proof that no longer supported route exists. No artificial detours were added to meet the requested 15-step threshold; the available evidence does not establish a chemically justified route of that depth.

## Interface and deployed-catalog checks

- Production `GET /api/reaction_planner` returned HTTP 200 and 13 reaction rules, including `fischer-esterification`.
- Auto mode was selected for route searches. In the esterification case, the two starting materials remained distinct from the target.
- The four-step route showed 2D structures, labels, ordered step cards, reaction arrows, and per-step condition text.
- On a fresh load, the 3D inspector checkbox was unchecked and its panel hidden.
- Reaction explanations were hidden initially, displayed when the checkbox was enabled, and hidden again when disabled.
- Searching the reagent catalogue for `sulfuric` returned the Fischer-esterification catalyst entry.
- At nominal viewport widths 375, 724, and 1280 CSS pixels, `documentElement.scrollWidth` equaled `documentElement.clientWidth`; no horizontal overflow was observed.
- After failed searches and parser failures, no stale route cards remained. Unsupported cases were visibly reported rather than shown as successful synthesis.
- The long generated systematic name for the cholesterol identity case was displayed alongside its structure in the desktop workspace; no horizontal overflow was observed at that layout.
- The browser logged HTTP 422 responses for expected unsupported-chemistry/parser cases; these were surfaced as UI errors, not successful routes.

## Campaign conclusion and scope

Of the 20 requested case entries, four returned routes (three non-identity routes and one zero-step identity), fourteen returned `unsupported_chemistry`, and two failed at exact target-name parsing. The routes found were ethene hydrogenation, Fischer esterification, cholesterol identity, and the four-step benzamide sequence. Every proposed route was structurally checked by the production engine; this is not experimental validation.

The observed unsupported outcomes chiefly reflect missing reaction coverage: alcohol oxidation/reduction, aromatic substitution/acylation/alkylation, phenol- or amine-selective acylation, Kolbe–Schmitt carboxylation, carbon–carbon bond construction, Strecker synthesis and stereochemical resolution, and heterocycle construction. The paclitaxel and vancomycin searches never reached the planner because OPSIN could not parse those exact names. Consequently, this campaign does not measure large-target search scalability or prove that any target is chemically unreachable.

The exact-name tests used browser interaction with the deployed website. Where a route was returned, its final canonical molecular graph was compared with the parsed target, and the route's per-step atom-balance, charge-balance, and provenance results were inspected. Graph validity and balanced bookkeeping do not establish kinetic, thermodynamic, experimental, or substrate-selectivity feasibility.
