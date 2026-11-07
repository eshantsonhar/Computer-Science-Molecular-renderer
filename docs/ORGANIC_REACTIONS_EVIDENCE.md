# Organic Reactions: evidence, scope, and implementation limits

## Evidence classification and research boundary

The initial reaction set contains two exact educational exemplars involving ethanoyl (acetyl) chloride. The references below state the reactants, products, qualitative conditions, coproducts, and addition-elimination mechanism for those examples.

These are secondary instructional mechanism pages, not peer-reviewed primary papers or checked experimental procedures. A search of Organic Syntheses records did not verify a primary procedure for either exact combination. Consequently, the application labels the evidence as secondary-source and does not claim that a primary procedure, yield, reaction rate, or experimental reproducibility was verified. The narrowly fixed substrates are an intentional restriction; the source's broader teaching generalizations are not encoded as reaction templates.

## Implemented transformations

### Acetyl chloride ammonolysis to acetamide

**Exact supported inputs:** one user-supplied ethanoyl chloride (`CC(=O)Cl`) and two explicitly authorized ammonia equivalents (`N`).

**Net transformation:**

```text
CH3COCl + 2 NH3 -> CH3CONH2 + NH4Cl
```

**Conditions and mechanism:** the source describes cold, concentrated ammonia solution and reports that the reaction is violent. Ammonia attacks the acyl carbon; collapse of the tetrahedral intermediate expels chloride; excess ammonia captures the acid equivalent as ammonium chloride. The planner represents one ammonia nitrogen in ethanamide and the second in ammonium, with one proton transferred between those reagent equivalents.

**Products and atom accounting:** ethanamide is the desired product; ammonium and chloride are both explicit coproduct components. The two carbon atoms and carbonyl oxygen originate in the allowed organic starting material. Both product nitrogens and all reagent-derived hydrogens originate in the explicitly authorized ammonia equivalents. All atoms, isotopes, formal charges, and source identifiers are checked across the complete reactant and product graphs.

**Safety notice:** the source describes a violent reaction. Acetyl chloride and concentrated ammonia present serious corrosive and exposure hazards. This is a hazard notice, not an experimental instruction.

**Scope and exclusions:** only the exact acetyl chloride graph and ammonia are accepted. Primary amines, water, other acid chlorides, multiple acyl sites, and competing nucleophiles are not represented. The rule does not predict whether an alternative nucleophile or side reaction dominates in an unmodeled mixture.

### Acetyl chloride ethanolysis to ethyl acetate

**Exact supported inputs:** one user-supplied ethanoyl chloride (`CC(=O)Cl`) and one user-supplied ethanol (`CCO`). Ethanol is an organic atom donor and must be present in the starting-material inventory.

**Net transformation:**

```text
CH3COCl + CH3CH2OH -> CH3COOCH2CH3 + HCl
```

**Conditions and mechanism:** the source describes cold ethanol, an instantaneous and very exothermic reaction, and hydrogen chloride evolution. Ethanol oxygen attacks the acyl carbon; chloride is displaced; the alcohol proton is accounted for in HCl.

**Products and atom accounting:** ethyl ethanoate is the desired product and hydrogen chloride is an explicit coproduct. The acyl atoms originate in ethanoyl chloride; the ethoxy carbons, oxygen, and hydrogens originate in user-supplied ethanol. Atom, isotope, formal-charge, and provenance conservation are checked on explicit-hydrogen graphs.

**Safety notice:** the source describes a very exothermic reaction with HCl gas evolution. Acetyl chloride and hydrogen chloride present serious corrosive and exposure hazards. This is a hazard notice, not an experimental instruction.

**Scope and exclusions:** only the exact acetyl chloride and ethanol graphs are accepted. Other alcohols, water, other acid chlorides, and competing nucleophiles are not represented. Conditions are qualitative because the source does not establish a quantitative procedure in the cited material.

## Reaction rules and references

| Rule ID | Transformation and evidence supported by the reference |
|---|---|
| `acetyl-chloride-ammonolysis` | Ethanoyl chloride + cold concentrated ammonia gives ethanamide and ammonium chloride; the page describes the addition-elimination mechanism and excess-ammonia neutralization. [Chemguide: reaction of acyl chlorides with ammonia](https://www.chemguide.co.uk/mechanisms/addelim/ammonia.html) |
| `acetyl-chloride-ethanolysis` | Ethanoyl chloride + cold ethanol gives ethyl ethanoate and HCl; the page describes the qualitative exothermicity and the acyl-substitution mechanism. [Chemguide: reaction of acyl chlorides with alcohols](https://www.chemguide.co.uk/mechanisms/addelim/alcohol.html) |
| Both rules | Background on the electrophilic acyl carbon, nucleophilic addition followed by elimination, and the general replacement of chloride. [Chemguide: acyl-chloride addition-elimination](https://www.chemguide.co.uk/mechanisms/addelim/whatis.html) |
| Negative-control rationale | The source describes water as a distinct nucleophile that hydrolyzes an acyl chloride rather than forming an ester or amide. Hydrolysis is not implemented as a planner rule. [Chemguide: reaction of acyl chlorides with water](https://www.chemguide.co.uk/mechanisms/addelim/water.html) |

## Evidence still missing

- A verified primary experimental procedure for either exact transformation, with quantities, work-up, isolated product, and product characterization.
- Evidence for broader substrate scope, reagent compatibility, chemoselectivity, or side-product distributions.
- Numerical temperatures, concentrations, rates, equilibrium constants, or yields.
- Evidence to support additional reaction families or multistep transformations.

The Organic Syntheses record for acetamide was inspected as a lead, but its accessible record did not verify that its procedure uses acetyl chloride and ammonia. A separately indexed acid-chloride/ammonia procedure could not be verified for product identity and full conditions. Neither was used to support a rule.

## Search and reporting semantics

The planner performs breadth-first forward search over the finite quantities supplied by the user, bounded to 20 steps and 1,000 expanded states. Starting-material inventories are limited to 20 total units. Reactions consume stoichiometric starting-material units and authorized ammonia equivalents; coproducts remain explicit in the route. These integer units are bookkeeping equivalents, not measured moles, mass, or an experimental material plan. Every atom is attributed to a starting-material or authorized-reagent ID. Heavy-atom indices are zero-based in the canonical SMILES graph parsed by RDKit; explicit hydrogens are attributed to their parent atom and per-parent ordinal. These indices are not screen coordinates from a drawing editor or indices from the user's original Molfile. The reported sequence is shortest only within the two exact rules above and the configured search limits. Auto mode derives the minimum ammonia amount required for requested acetamide units from the available exact acetyl chloride inventory; it cannot select among unsupported reagent systems. `no-supported-route` means no route was found in that subset; it does not mean that no chemical route exists.

## Entry names, catalogue, and interface

OPSIN is used only for name-to-structure parsing. The project does not include a locally validated structure-to-IUPAC naming engine. Names entered through the IUPAC field are retained; SMILES, Molfile, and editor entries are explicitly labeled `Verified IUPAC name unavailable`. No name is generated by RDKit. The local searchable reagent catalogue includes only ammonia, because that is the only separately selectable reagent in the implemented rule set. Expanding it without corresponding validated reaction rules would misleadingly imply applicability.

Reaction diagrams use a molecular 2D depiction of each returned SMILES graph, IUPAC labels when available, explicit plus signs, and the rule's qualitative conditions on the arrow. The 3D inspector is hidden by default and is opened by its checkbox or an `Inspect 3D` action. Neither the 2D depiction nor the generated 3D conformer establishes reaction feasibility or experimental geometry.

## Geometry endpoint diagnosis

The local static preview at `http://127.0.0.1:8765` returns HTTP 404 with `text/html` for `/api/geometry`: Python's static HTTP server serves no Vercel Python functions. That is the observed source of the `<!DOCTYPE ...` response in that preview configuration. Run `vercel dev` to exercise the repository's functions locally. The browser client now checks status and content type before parsing JSON. This local diagnosis does not verify a remote deployment; production status requires the deployment URL and its live function responses.

RDKit sanitization establishes graph validity, not reaction feasibility. The reaction rules add a narrow, source-cited transformation and qualitative condition gate, but the application does not model kinetics, thermodynamics, yields, conversion, side reactions, safety, experimental execution, or competition from an unrepresented condition. Force-field geometry is only a conformer model and is not reaction evidence.

## Not investigated or implemented

No general alkene/alkyne reactions, alcohol oxidation, carbonyl additions, carboxylic-acid activation, substitution/elimination, aromatic substitution, C-C coupling, redox chemistry, protection, deprotection, or organometallic chemistry is included. These families require independent evidence review, scoped templates, selectivity handling, atom accounting, and negative tests before acceptance.
