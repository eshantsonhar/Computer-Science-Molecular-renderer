# Organic Reactions Phase 2: implementation and verification

**Run date:** 2026-11-12  
**Environment:** local source tree and local website at `http://127.0.0.1:8765/pages/organic_reactions.html`  
**Route mode:** Auto; challenge names were entered through the website as IUPAC-name inputs.

This report records the local implementation and its tested scope. It is not a production deployment report, experimental validation, or a claim of general synthesis capability. The local catalogue contains 29 rules: the initial 13 plus 16 Phase 2 additions. Production was not updated by these local changes at the time of this report.

## Added reaction rules and actual applicability

The rules are constrained graph transformations, not generic reaction predictions. Conditions below are catalogue-level descriptions, not operating procedures.

| Rule ID | Transformation and modelled scope | Reagents/conditions and limits |
|---|---|---|
| `primary-alcohol-to-aldehyde` | Saturated acyclic aliphatic primary alcohol -> aldehyde | NaOCl with catalytic TEMPO under controlled buffered conditions. Other heteroatoms/unsaturation and competing oxidizable groups are rejected; overoxidation and conversion are not predicted. |
| `primary-alcohol-to-carboxylic-acid` | Simple primary alcohol -> carboxylic acid, distinct from aldehyde formation | Two equivalents H2O2 with catalytic tungstate; saturated acyclic aliphatic alcohols only. |
| `secondary-alcohol-to-ketone` | Simple secondary alcohol -> ketone without carbon-skeleton change | H2O2/tungstate; one saturated acyclic aliphatic alcohol and no competing unsaturation. |
| `aldehyde-to-carboxylic-acid` | Simple aldehyde -> carboxylic acid | Aqueous H2O2; other heteroatoms and non-aromatic unsaturation are excluded. |
| `aldehyde-hydrogenation` | Simple aldehyde -> primary alcohol | H2/Pd-C; no other reducible groups, aromatic-ring hydrogenation, or selectivity prediction. |
| `benzene-nitration` | Benzene -> nitrobenzene | Nitric/sulfuric acid system; unsubstituted benzene only. Directing effects and substituted-ring regioselectivity are deliberately unsupported. |
| `benzene-friedel-crafts-acylation` | Benzene -> acetophenone | Acetyl chloride/stoichiometric AlCl3. Only this benzene/acetyl combination is matched; AlCl3 complexation and work-up are not represented in net atom bookkeeping. |
| `benzene-friedel-crafts-ethylation` | Benzene -> ethylbenzene | Chloroethane/AlCl3. Other alkylating agents, rearrangements, and substituted arenes are excluded; excess benzene/limiting alkylating reagent is stated to reduce polyalkylation, but no product ratio is predicted. |
| `phenolic-o-acetylation` | A single hydroxybenzoic-acid site pattern -> phenolic acetate, retaining CO2H | Acetic anhydride with catalytic acid and mild heating; one phenolic OH and one carboxylic acid on an otherwise unsubstituted ring. |
| `aniline-n-acetylation` | One aminophenol site pattern -> N-acetyl product, retaining phenolic OH | Acetic anhydride under mild conditions; one primary aniline and one phenolic OH only. The rule does not predict general N/O-acylation selectivity or product ratios. |
| `phenol-deprotonation` | Unsubstituted phenol -> phenoxide | One equivalent NaOH; simple phenol only. |
| `kolbe-schmitt-carboxylation` | Simple phenoxide + CO2 -> salicylate at equivalent ortho positions | Heat and elevated CO2 pressure are listed; acidification is a separate HCl step. Substituted-ring regioselectivity is not handled. |
| `strecker-imine-formation` | Simple aliphatic aldehyde + ammonia -> imine + water | Water-removing conditions; equilibrium and physical water removal are not simulated. |
| `strecker-cyanide-addition` | Simple aldehyde-derived imine + HCN -> alpha-aminonitrile | Acid-promoted addition; no chiral catalyst or asymmetric induction. The new stereocenter remains unspecified. |
| `aminonitrile-hydrolysis` | Simple acyclic primary alpha-aminonitrile -> amino-acid carboxylate + ammonia | Aqueous base and heat; neutral amino acid requires separate acidification. |
| `paal-knorr-pyrrole-synthesis` | Unsubstituted butane-1,4-dial + ammonia -> pyrrole + two waters | Neutral or weakly acidic conditions; substituted 1,4-dicarbonyls/amines and strong-acid furan competition are outside the model. |

Reference entries are attached to the rules. Some textbook entries explicitly have unverified page ranges; the named-reaction references link to the Organic Chemistry Portal. These sources support established reaction classes, not the full substrate scope, yield, kinetics, or operational feasibility represented by every rule.

## Required Auto-mode challenges

All nine exact-name challenges were entered through the local website UI in Auto mode. Each found the requested product graph:

| ID | Input -> target | Auto result |
|---|---|---|
| A1 | `ethanol` -> `ethanoic acid` | One-step primary-alcohol-to-acid oxidation; H2O2/tungstate conditions. The separate aldehyde rule does not silently substitute ethanal as the acid product. |
| A2 | `propan-2-ol` -> `propanone` | One-step secondary-alcohol oxidation. |
| A3 | `benzene` -> `nitrobenzene` | One-step nitration, restricted to unsubstituted benzene. |
| A4 | `2-hydroxybenzoic acid` -> `2-acetyloxybenzoic acid` | One-step phenolic O-acetylation; carboxylic acid retained. |
| A5 | `4-aminophenol` -> `N-(4-hydroxyphenyl)acetamide` | One-step N-acetylation; phenolic OH retained. |
| A6 | `benzene` -> `1-phenylethan-1-one` | One-step Friedel-Crafts acetylation. |
| A7 | `benzene` -> `ethylbenzene` | One-step Friedel-Crafts ethylation. |
| A8 | `phenol` + `carbon dioxide` -> `2-hydroxybenzoic acid` | Three steps: phenoxide formation, Kolbe-Schmitt carboxylation, acidification. Carbon tracing shows salicylate's ring from phenol and added carboxyl carbon from CO2. |
| A9 | `benzaldehyde` -> `phenylmethanol` | One-step aldehyde hydrogenation. |

The route graphs matched the requested target graphs in the browser workflow. A successful graph match and balanced atom bookkeeping are not evidence of experimental conversion or selectivity outside the encoded substrate gates.

## Regression and additional chemistry checks

The four earlier supported routes remain in the local regression baseline:

- `ethene` -> `ethane`: one catalytic hydrogenation step.
- `ethanoic acid` + `ethanol` -> `ethyl ethanoate`: Fischer esterification with explicit water coproduct and reversible-equilibrium caveat.
- `cholest-5-en-3beta-ol` -> itself: zero-step identity route, with the input stereochemistry retained.
- `ethyl benzoate` -> `benzamide`: four displayed steps (saponification, acidification, acid-chloride formation, ammonolysis). Its intermediate sequence, HCl/ammonia bookkeeping, coproducts, provenance, and target graph were previously inspected; this remains a graph/bookkeeping validation, not a practical synthesis assessment.

The focused local planner suite passes: **29 tests and 40 subtests**. Added checks cover each new rule, expected product graphs, selected negative substrate cases, atom/charge balance, explicit coproducts, reagent-derived atoms, and provenance. The three-feedstock Strecker route to unspecified-stereochemistry `2-aminopropanoic acid` was also exercised through the website: four transformations form the imine, add cyanide, hydrolyze the nitrile, and acidify. Carbon/nitrogen provenance traces to ethanal, HCN, and ammonia; the carboxylate oxygens include atoms supplied by water. A separate `(2S)-2-aminopropanoic acid` request remains unsupported: the planner does not label the racemic/unspecified product as enantiopure.

As a separate supported heterocycle challenge, butane-1,4-dial + ammonia -> `1H-pyrrole` succeeds by Paal-Knorr condensation with two explicit water coproducts. The rule is intentionally limited to the unsubstituted 1,4-dialdehyde and ammonia.

## Advanced challenges and limits

| Challenge | Observed result | Why no stronger claim is made |
|---|---|---|
| Ibuprofen from `1-(2-methylpropyl)benzene` | Names parse; Auto found no supported route to `2-[4-(2-methylpropyl)phenyl]propanoic acid`. | No para-selective acylation of a substituted ring, ketone-to-secondary-alcohol reduction, or BHC carbonylation rule is present. No intermediate was substituted for ibuprofen. |
| Racemic alanine from ethanal + HCN + ammonia | Four-step Strecker route to unspecified-stereochemistry alanine succeeds. | Three feedstocks contribute atoms, but this is not a branched route whose independently synthesized intermediates later converge. |
| `(2S)-2-aminopropanoic acid` | Parsed; no route found. | No asymmetric Strecker catalyst or resolution/product-liberation sequence is represented. |
| 2-Phenylethan-1-ol from benzene + ethene | Names parse; no route found. | No ethylene-oxide/side-chain homologation sequence or corresponding carbon-skeleton transformations are represented. |
| Caffeine from 1,3-dimethylurea + cyanoacetic acid | Names parse; no route found. | Purine-ring construction, correct N-connectivity, and regioselective N-methylation are absent; no direct conversion is invented. |
| Fifteen-step benchmark | No documented route of 15 or more distinct transformations was independently discovered and validated. The longest verified multistep results remain four steps. | The search limit is 20 steps, but the tested route set lacks the broad reusable chemistry needed for a credible deep route. This is a reaction-coverage/planning limitation, not evidence that no such chemistry exists. |
| Independent convergent branches | Not demonstrated. | Multi-feedstock Strecker and Kolbe-Schmitt tests establish incorporation from multiple inputs, but not separate branches that later converge. |

The 20-step configured bound is not evidence that the planner can discover 20-step routes. No artificial transformations or preselected literature route were inserted to inflate depth.

## Large-molecule exact-name parsing

The exact systematic names below are PubChem `IUPACName` property values (PubChem compound records and CID shown). They were entered unchanged as both starting material and target in the local website, with Auto selected. Both were accepted by OPSIN; each produced a zero-step identity route.

| Compound/source | Exact name entered | Website and independent local graph check |
|---|---|---|
| [Paclitaxel, PubChem CID 36314](https://pubchem.ncbi.nlm.nih.gov/compound/36314) | `[(1S,2S,3R,4S,7R,9S,10S,12R,15S)-4,12-diacetyloxy-15-[(2R,3S)-3-benzamido-2-hydroxy-3-phenylpropanoyl]oxy-1,9-dihydroxy-10,14,17,17-tetramethyl-11-oxo-6-oxatetracyclo[11.3.1.03,10.04,7]heptadec-13-en-2-yl] benzoate` | Website formula `C47H51NO14`; local RDKit InChIKey `RCINICONZNJXQF-MZXODVADSA-N`, matching PubChem. |
| [Vancomycin, PubChem CID 14969](https://pubchem.ncbi.nlm.nih.gov/compound/14969) | `(1S,2R,18R,19R,22S,25R,28R,40S)-48-[(2S,3R,4S,5S,6R)-3-[(2S,4S,5S,6S)-4-amino-5-hydroxy-4,6-dimethyloxan-2-yl]oxy-4,5-dihydroxy-6-(hydroxymethyl)oxan-2-yl]oxy-22-(2-amino-2-oxoethyl)-5,15-dichloro-2,18,32,35,37-pentahydroxy-19-[[(2R)-4-methyl-2-(methylamino)pentanoyl]amino]-20,23,26,42,44-pentaoxo-7,13-dioxa-21,24,27,41,43-pentazaoctacyclo[26.14.2.23,6.214,17.18,12.129,33.010,25.034,39]pentaconta-3,5,8(48),9,11,14,16,29(45),30,32,34(39),35,37,46,49-pentadecaene-40-carboxylic acid` | Website formula `C66H75Cl2N9O24`; local RDKit InChIKey `MYPYJXKWCTUITO-LYRMYLQWSA-N`, matching PubChem. |

The website's bounded ETKDG/MMFF force-field optimization did **not** converge within 500 iterations for either large graph; the UI displayed that warning. This is classified as successful name parsing and graph construction with a geometry-optimization warning, not a parser failure or a validated experimental conformation. The structure-naming service also reported no generated IUPAC name for these graphs; that does not undo successful parsing of the user-supplied names.

## Verification boundary

The local website challenges and focused tests establish that the specific encoded graph transformations run, produce the tested graphs, and preserve the modeled atom sources/coproduct bookkeeping. They do not establish yield, rate, equilibrium position, operational safety, or broad substrate scope. The 15-step and independent convergent-synthesis requirements remain unmet; production has not yet been updated with this local catalogue.
