import json
from collections import Counter, deque
from http.server import BaseHTTPRequestHandler
from typing import Any

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

from api.geometry import GeometryInputError, MAX_HEAVY_ATOMS


MAX_REQUEST_BYTES = 1_000_000
MAX_MATERIAL_ENTRIES = 20
MAX_SEARCH_DEPTH = 20
MAX_SEARCH_STATES = 1_000

RULES = (
    {
        "id": "acetyl-chloride-ammonolysis",
        "name": "Acetyl chloride ammonolysis to acetamide",
        "family": "nucleophilic acyl substitution",
        "classification": "Secondary-source exemplar; no primary procedure verified",
        "reactants": [
            {"smiles": "CC(=O)Cl", "role": "allowed organic starting material", "quantity": 1},
            {"smiles": "N", "role": "user-authorized inorganic reagent", "quantity": 2},
        ],
        "products": [
            {"smiles": "CC(N)=O", "role": "desired primary amide", "quantity": 1},
            {"smiles": "[NH4+]", "role": "ammonium coproduct component", "quantity": 1},
            {"smiles": "[Cl-]", "role": "chloride coproduct component", "quantity": 1},
        ],
        "principalProductSmiles": "CC(N)=O",
        "conditions": "Cold, concentrated ammonia; excess ammonia captures HCl.",
        "shortDescription": "Ammonia substitutes for chloride at the acyl carbon.",
        "safetyNotes": "The cited source describes this reaction as violent. Acetyl chloride and concentrated ammonia present serious corrosive and exposure hazards; this notice is not an experimental procedure.",
        "stoichiometry": "CH3COCl + 2 NH3 -> CH3CONH2 + NH4Cl",
        "selectivity": "The nucleophile is explicitly ammonia; amines, water, and other nucleophiles are not interchangeable with it.",
        "limitations": [
            "Only acetyl chloride is accepted; no general acid-chloride substrate scope is asserted.",
            "No competition with water or other nucleophiles is modeled.",
            "The cited source is an educational mechanism reference; a primary experimental procedure for this exact example was not verified.",
            "No yield, rate, equilibrium, or quantitative feasibility prediction is made.",
        ],
        "referenceIds": ["chemguide-ammonia", "chemguide-general-addition-elimination"],
    },
    {
        "id": "acetyl-chloride-ethanolysis",
        "name": "Acetyl chloride ethanolysis to ethyl acetate",
        "family": "nucleophilic acyl substitution",
        "classification": "Secondary-source exemplar; no primary procedure verified",
        "reactants": [
            {"smiles": "CC(=O)Cl", "role": "allowed organic starting material", "quantity": 1},
            {"smiles": "CCO", "role": "allowed organic starting material and atom donor", "quantity": 1},
        ],
        "products": [
            {"smiles": "CCOC(C)=O", "role": "desired ester", "quantity": 1},
            {"smiles": "Cl", "role": "hydrogen chloride coproduct", "quantity": 1},
        ],
        "principalProductSmiles": "CCOC(C)=O",
        "conditions": "Cold ethanol; exothermic, with HCl evolution.",
        "shortDescription": "Ethanolysis of ethanoyl chloride forms ethyl ethanoate.",
        "safetyNotes": "The cited source describes this reaction as very exothermic with HCl gas evolution. Acetyl chloride and hydrogen chloride present serious corrosive and exposure hazards; this notice is not an experimental procedure.",
        "stoichiometry": "CH3COCl + CH3CH2OH -> CH3COOCH2CH3 + HCl",
        "selectivity": "Ethanol is the sole modeled oxygen nucleophile; no competing nucleophile is modeled.",
        "limitations": [
            "Only acetyl chloride and ethanol are accepted; no general alcohol or acid-chloride scope is asserted.",
            "Water, other alcohols, and other nucleophiles are not included in the rule.",
            "The cited source is an educational mechanism reference; a primary experimental procedure for this exact example was not verified.",
            "No yield, rate, equilibrium, or quantitative feasibility prediction is made.",
        ],
        "referenceIds": ["chemguide-alcohol", "chemguide-general-addition-elimination"],
    },
)


class PlannerInputError(ValueError):
    pass


def _read_molecule(smiles: Any, label: str) -> Chem.Mol:
    if not isinstance(smiles, str) or not smiles.strip() or len(smiles) > 2_000:
        raise PlannerInputError(f"{label} must contain a SMILES string of at most 2,000 characters.")
    molecule = Chem.MolFromSmiles(smiles.strip(), sanitize=True)
    if molecule is None or molecule.GetNumAtoms() == 0:
        raise PlannerInputError(f"{label} is not a valid, sanitizable molecular structure.")
    if molecule.GetNumHeavyAtoms() > MAX_HEAVY_ATOMS:
        raise PlannerInputError(
            f"{label} exceeds the {MAX_HEAVY_ATOMS}-heavy-atom planner limit."
        )
    Chem.AssignStereochemistry(molecule, force=True, cleanIt=True)
    return molecule


def _canonical_smiles(molecule: Chem.Mol) -> str:
    return Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)


def _compound_summary(molecule: Chem.Mol, name: str | None = None) -> dict[str, Any]:
    bond_stereochemistry = [
        {"bondIndex": bond.GetIdx(), "label": str(bond.GetStereo())}
        for bond in molecule.GetBonds()
        if bond.GetStereo() != Chem.BondStereo.STEREONONE
    ]
    result = {
        "canonicalSmiles": _canonical_smiles(molecule),
        "formula": rdMolDescriptors.CalcMolFormula(molecule),
        "molecularWeight": round(Descriptors.MolWt(molecule), 4),
        "formalCharge": sum(atom.GetFormalCharge() for atom in molecule.GetAtoms()),
        "stereochemistry": [
            {"atomIndex": atom.GetIdx(), "label": atom.GetProp("_CIPCode")}
            for atom in molecule.GetAtoms()
            if atom.HasProp("_CIPCode")
        ],
        "unspecifiedStereocentres": [
            atom_index
            for atom_index, label in Chem.FindMolChiralCenters(
                molecule, includeUnassigned=True, includeCIP=True
            )
            if label == "?"
        ],
        "bondStereochemistry": bond_stereochemistry,
    }
    if name:
        result["name"] = name
    return result


def _compound_entries(
    payload: Any, key: str, *, must_be_organic: bool
) -> list[dict[str, Any]]:
    entries = payload.get(key)
    if not isinstance(entries, list) or not entries or len(entries) > MAX_MATERIAL_ENTRIES:
        raise PlannerInputError(
            f"{key} must contain between 1 and {MAX_MATERIAL_ENTRIES} compounds."
        )

    normalized = []
    seen_ids = set()
    total_quantity = 0
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise PlannerInputError(f"{key} entry {index + 1} must be an object.")
        quantity = entry.get("quantity", 1)
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 20:
            raise PlannerInputError(
                f"{key} entry {index + 1} quantity must be an integer from 1 to 20."
            )
        total_quantity += quantity
        if total_quantity > MAX_MATERIAL_ENTRIES:
            raise PlannerInputError(
                f"{key} may contain at most {MAX_MATERIAL_ENTRIES} total compound units."
            )

        molecule = _read_molecule(entry.get("smiles"), f"{key} entry {index + 1}")
        if must_be_organic and not any(atom.GetAtomicNum() == 6 for atom in molecule.GetAtoms()):
            raise PlannerInputError(f"{key} entries must contain at least one carbon atom.")
        compound_id = entry.get("id", f"{key}-{index + 1}")
        if not isinstance(compound_id, str) or not compound_id or len(compound_id) > 100:
            raise PlannerInputError(f"{key} entry {index + 1} has an invalid id.")
        if compound_id in seen_ids:
            raise PlannerInputError(f"{key} contains duplicate entry id {compound_id!r}.")
        seen_ids.add(compound_id)
        name = entry.get("name")
        if name is not None and (not isinstance(name, str) or len(name) > 500):
            raise PlannerInputError(f"{key} entry {index + 1} has an invalid name.")
        normalized.append(
            {
                **_compound_summary(molecule, name),
                "id": compound_id,
                "quantity": quantity,
            }
        )
    return normalized


def _reagent_inventory(payload: Any) -> dict[str, int]:
    reagents = payload.get("reagents", {})
    if not isinstance(reagents, dict):
        raise PlannerInputError("reagents must be an object.")
    unsupported = set(reagents) - {"ammonia"}
    if unsupported:
        raise PlannerInputError(
            "Unsupported reagent inventory: " + ", ".join(sorted(unsupported)) + "."
        )
    quantity = reagents.get("ammonia", 0)
    if isinstance(quantity, bool) or not isinstance(quantity, int) or not 0 <= quantity <= 100:
        raise PlannerInputError("reagents.ammonia must be an integer from 0 to 100 equivalents.")
    return {"ammonia": quantity}


def _source_atom(
    source_kind: str, source_id: str, atom_index: int, source_name: str
) -> dict[str, Any]:
    return {
        "sourceType": source_kind,
        "sourceId": source_id,
        "sourceName": source_name,
        "atomIndex": atom_index,
    }


def _explicit_source_molecule(
    smiles: str, source_kind: str, source_id: str, source_name: str
) -> Chem.Mol:
    molecule = Chem.AddHs(_read_molecule(smiles, "Reaction reactant"))
    hydrogen_ordinals: Counter[int] = Counter()
    for atom in molecule.GetAtoms():
        if atom.GetAtomicNum() == 1 and atom.GetDegree() == 1:
            parent = atom.GetNeighbors()[0]
            hydrogen_ordinals[parent.GetIdx()] += 1
            origin = {
                "sourceType": source_kind,
                "sourceId": source_id,
                "sourceName": source_name,
                "parentAtomIndex": parent.GetIdx(),
                "hydrogenOrdinal": hydrogen_ordinals[parent.GetIdx()],
            }
        else:
            origin = _source_atom(
                source_kind, source_id, atom.GetIdx(), source_name
            )
        atom.SetProp(
            "_atomViewOrigin",
            json.dumps(origin, separators=(",", ":")),
        )
    return molecule


def _origin(atom: Chem.Atom) -> dict[str, Any]:
    if not atom.HasProp("_atomViewOrigin"):
        raise PlannerInputError("An atom lost its source identity during the transformation.")
    return json.loads(atom.GetProp("_atomViewOrigin"))


def _atom_ref(atom: Chem.Atom) -> dict[str, Any]:
    return {"element": atom.GetSymbol(), **_origin(atom)}


def _find_acetyl_chloride_bonds(molecule: Chem.Mol) -> tuple[int, int]:
    carbonyl_carbons = []
    for atom in molecule.GetAtoms():
        if atom.GetAtomicNum() != 6:
            continue
        oxygen_double_bond = any(
            bond.GetBondType() == Chem.BondType.DOUBLE
            and bond.GetOtherAtom(atom).GetAtomicNum() == 8
            for bond in atom.GetBonds()
        )
        chlorine = next(
            (
                neighbor.GetIdx()
                for neighbor in atom.GetNeighbors()
                if neighbor.GetAtomicNum() == 17
                and molecule.GetBondBetweenAtoms(atom.GetIdx(), neighbor.GetIdx()).GetBondType()
                == Chem.BondType.SINGLE
            ),
            None,
        )
        if oxygen_double_bond and chlorine is not None:
            carbonyl_carbons.append((atom.GetIdx(), chlorine))
    if len(carbonyl_carbons) != 1 or _canonical_smiles(Chem.RemoveHs(molecule)) != "CC(=O)Cl":
        raise PlannerInputError("This reaction rule accepts acetyl chloride only.")
    return carbonyl_carbons[0]


def _summarize_products(
    reactant_molecules: list[Chem.Mol], product_graph: Chem.Mol
) -> list[dict[str, Any]]:
    Chem.SanitizeMol(product_graph)
    expected_atoms = Counter(
        (atom.GetAtomicNum(), atom.GetIsotope())
        for molecule in reactant_molecules
        for atom in molecule.GetAtoms()
    )
    expected_origins = [
        atom.GetProp("_atomViewOrigin")
        for molecule in reactant_molecules
        for atom in molecule.GetAtoms()
    ]
    fragments = Chem.GetMolFrags(product_graph, asMols=True, sanitizeFrags=True)
    actual_atoms = Counter(
        (atom.GetAtomicNum(), atom.GetIsotope())
        for fragment in fragments
        for atom in fragment.GetAtoms()
    )
    actual_origins = [
        atom.GetProp("_atomViewOrigin")
        for fragment in fragments
        for atom in fragment.GetAtoms()
        if atom.HasProp("_atomViewOrigin")
    ]
    if expected_atoms != actual_atoms or sorted(expected_origins) != sorted(actual_origins):
        raise PlannerInputError(
            "The proposed reaction failed explicit atom, isotope, or provenance conservation."
        )

    reactant_charge = sum(
        atom.GetFormalCharge()
        for molecule in reactant_molecules
        for atom in molecule.GetAtoms()
    )
    product_charge = sum(
        atom.GetFormalCharge()
        for fragment in fragments
        for atom in fragment.GetAtoms()
    )
    if reactant_charge != product_charge:
        raise PlannerInputError("The proposed reaction did not conserve total formal charge.")

    products = []
    for fragment in fragments:
        molecule_without_hydrogens = Chem.RemoveHs(fragment)
        summary = _compound_summary(molecule_without_hydrogens)
        summary["atoms"] = [
            {
                "productAtomIndex": atom.GetIdx(),
                "element": atom.GetSymbol(),
                "isotope": atom.GetIsotope(),
                "formalCharge": atom.GetFormalCharge(),
                "origin": _origin(atom),
            }
            for atom in fragment.GetAtoms()
        ]
        products.append(summary)
    return products


def _run_ammonolysis(
    acid_chloride: dict[str, Any], ammonia_start: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol]]:
    acid = _explicit_source_molecule(
        acid_chloride["canonicalSmiles"],
        "startingMaterial",
        acid_chloride["sourceId"],
        acid_chloride["sourceName"],
    )
    ammonia_for_product = _explicit_source_molecule(
        "N", "reagent", f"ammonia-equivalent-{ammonia_start}", "authorized ammonia"
    )
    ammonia_for_salt = _explicit_source_molecule(
        "N",
        "reagent",
        f"ammonia-equivalent-{ammonia_start + 1}",
        "authorized ammonia",
    )
    reactants = [acid, ammonia_for_product, ammonia_for_salt]
    carbonyl_carbon, chloride_index = _find_acetyl_chloride_bonds(acid)
    product_nitrogen = next(atom.GetIdx() for atom in ammonia_for_product.GetAtoms() if atom.GetAtomicNum() == 7)
    salt_nitrogen = next(atom.GetIdx() for atom in ammonia_for_salt.GetAtoms() if atom.GetAtomicNum() == 7)
    transferred_hydrogen = next(
        atom.GetIdx()
        for atom in ammonia_for_product.GetAtomWithIdx(product_nitrogen).GetNeighbors()
        if atom.GetAtomicNum() == 1
    )
    product_nitrogen_offset = acid.GetNumAtoms()
    salt_nitrogen_offset = acid.GetNumAtoms() + ammonia_for_product.GetNumAtoms()
    product_graph = Chem.RWMol(Chem.CombineMols(Chem.CombineMols(acid, ammonia_for_product), ammonia_for_salt))
    source_chloride = product_graph.GetAtomWithIdx(chloride_index)
    source_carbon = product_graph.GetAtomWithIdx(carbonyl_carbon)
    source_nitrogen = product_graph.GetAtomWithIdx(product_nitrogen + product_nitrogen_offset)
    source_salt_nitrogen = product_graph.GetAtomWithIdx(salt_nitrogen + salt_nitrogen_offset)
    source_hydrogen = product_graph.GetAtomWithIdx(transferred_hydrogen + product_nitrogen_offset)
    changes = [
        {"change": "broken", "from": _atom_ref(source_carbon), "to": _atom_ref(source_chloride)},
        {"change": "formed", "from": _atom_ref(source_carbon), "to": _atom_ref(source_nitrogen)},
        {"change": "broken", "from": _atom_ref(source_nitrogen), "to": _atom_ref(source_hydrogen)},
        {"change": "formed", "from": _atom_ref(source_salt_nitrogen), "to": _atom_ref(source_hydrogen)},
    ]
    product_graph.RemoveBond(carbonyl_carbon, chloride_index)
    product_graph.AddBond(
        carbonyl_carbon, product_nitrogen + product_nitrogen_offset, Chem.BondType.SINGLE
    )
    product_graph.RemoveBond(
        product_nitrogen + product_nitrogen_offset,
        transferred_hydrogen + product_nitrogen_offset,
    )
    product_graph.AddBond(
        salt_nitrogen + salt_nitrogen_offset,
        transferred_hydrogen + product_nitrogen_offset,
        Chem.BondType.SINGLE,
    )
    product_graph.GetAtomWithIdx(chloride_index).SetFormalCharge(-1)
    product_graph.GetAtomWithIdx(salt_nitrogen + salt_nitrogen_offset).SetFormalCharge(1)
    products = _summarize_products(reactants, product_graph.GetMol())
    return products, changes, reactants


def _run_ethanolysis(
    acid_chloride: dict[str, Any], ethanol_material: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol]]:
    acid = _explicit_source_molecule(
        acid_chloride["canonicalSmiles"],
        "startingMaterial",
        acid_chloride["sourceId"],
        acid_chloride["sourceName"],
    )
    ethanol = _explicit_source_molecule(
        ethanol_material["canonicalSmiles"],
        "startingMaterial",
        ethanol_material["sourceId"],
        ethanol_material["sourceName"],
    )
    reactants = [acid, ethanol]
    carbonyl_carbon, chloride_index = _find_acetyl_chloride_bonds(acid)
    oxygen = next(
        atom.GetIdx()
        for atom in ethanol.GetAtoms()
        if atom.GetAtomicNum() == 8
        and any(neighbor.GetAtomicNum() == 1 for neighbor in atom.GetNeighbors())
    )
    ethanol_offset = acid.GetNumAtoms()
    oxygen_index = oxygen + ethanol_offset
    hydrogen_index = next(
        neighbor.GetIdx() + ethanol_offset
        for neighbor in ethanol.GetAtomWithIdx(oxygen).GetNeighbors()
        if neighbor.GetAtomicNum() == 1
    )
    product_graph = Chem.RWMol(Chem.CombineMols(acid, ethanol))
    source_carbon = product_graph.GetAtomWithIdx(carbonyl_carbon)
    source_chloride = product_graph.GetAtomWithIdx(chloride_index)
    source_oxygen = product_graph.GetAtomWithIdx(oxygen_index)
    source_hydrogen = product_graph.GetAtomWithIdx(hydrogen_index)
    changes = [
        {"change": "broken", "from": _atom_ref(source_carbon), "to": _atom_ref(source_chloride)},
        {"change": "formed", "from": _atom_ref(source_carbon), "to": _atom_ref(source_oxygen)},
        {"change": "broken", "from": _atom_ref(source_oxygen), "to": _atom_ref(source_hydrogen)},
        {"change": "formed", "from": _atom_ref(source_chloride), "to": _atom_ref(source_hydrogen)},
    ]
    product_graph.RemoveBond(carbonyl_carbon, chloride_index)
    product_graph.AddBond(carbonyl_carbon, oxygen_index, Chem.BondType.SINGLE)
    product_graph.RemoveBond(oxygen_index, hydrogen_index)
    product_graph.AddBond(chloride_index, hydrogen_index, Chem.BondType.SINGLE)
    products = _summarize_products(reactants, product_graph.GetMol())
    return products, changes, reactants


def _is_goal(inventory: dict[tuple[str, str, str], int], targets: list[dict[str, Any]]) -> bool:
    available = Counter()
    for lot, quantity in inventory.items():
        available[lot[0]] += quantity
    required = Counter()
    for target in targets:
        required[target["canonicalSmiles"]] += target["quantity"]
    return all(available[smiles] >= quantity for smiles, quantity in required.items())


def _target_is_still_required(
    inventory: dict[tuple[str, str, str], int],
    targets: list[dict[str, Any]],
    product_smiles: str,
) -> bool:
    available = sum(
        quantity
        for (smiles, _source_id, _source_name), quantity in inventory.items()
        if smiles == product_smiles
    )
    required = sum(
        target["quantity"]
        for target in targets
        if target["canonicalSmiles"] == product_smiles
    )
    return available < required


def _inventory_signature(
    inventory: dict[tuple[str, str, str], int], ammonia_equivalents: int
) -> tuple[Any, ...]:
    totals = Counter()
    for (smiles, _source_id, _source_name), quantity in inventory.items():
        totals[smiles] += quantity
    return (
        tuple(sorted(totals.items())),
        ammonia_equivalents,
    )


def _find_lot(
    inventory: dict[tuple[str, str, str], int], smiles: str
) -> tuple[str, str, str] | None:
    return next(
        (
            key
            for key in sorted(inventory)
            if key[0] == smiles and inventory[key] > 0
        ),
        None,
    )


def _add_products_to_inventory(
    inventory: dict[tuple[str, str, str], int],
    products: list[dict[str, Any]],
    step_number: int,
) -> None:
    for index, product in enumerate(products, start=1):
        source_name = product.get("name") or product["formula"]
        key = (
            product["canonicalSmiles"],
            f"step-{step_number}-product-{index}",
            source_name,
        )
        inventory[key] = inventory.get(key, 0) + 1


def _product_balance(reactants: list[Chem.Mol], products: list[dict[str, Any]]) -> dict[str, Any]:
    reactant_atoms = Counter(
        (atom.GetSymbol(), atom.GetIsotope())
        for molecule in reactants
        for atom in molecule.GetAtoms()
    )
    product_atoms = Counter()
    product_charge = 0
    for product in products:
        molecule = Chem.AddHs(
            _read_molecule(product["canonicalSmiles"], "Reaction product")
        )
        for atom in molecule.GetAtoms():
            product_atoms[(atom.GetSymbol(), atom.GetIsotope())] += 1
        product_charge += sum(atom.GetFormalCharge() for atom in molecule.GetAtoms())
    reactant_charge = sum(
        atom.GetFormalCharge() for molecule in reactants for atom in molecule.GetAtoms()
    )
    return {
        "atomBalanceChecked": reactant_atoms == product_atoms,
        "chargeBalanceChecked": reactant_charge == product_charge,
        "reactantAtomCounts": {f"{element}[{isotope}]": count for (element, isotope), count in sorted(reactant_atoms.items())},
        "productAtomCounts": {f"{element}[{isotope}]": count for (element, isotope), count in sorted(product_atoms.items())},
    }


def _route_step(
    rule: dict[str, Any],
    products: list[dict[str, Any]],
    changes: list[dict[str, Any]],
    reactants: list[Chem.Mol],
    step_number: int,
) -> dict[str, Any]:
    expected_reactants = Counter()
    for requirement in rule["reactants"]:
        canonical = _canonical_smiles(_read_molecule(requirement["smiles"], "Rule reactant"))
        expected_reactants[canonical] += requirement["quantity"]
    actual_reactants = Counter(
        _canonical_smiles(Chem.RemoveHs(molecule)) for molecule in reactants
    )
    if expected_reactants != actual_reactants:
        raise PlannerInputError("The generated reactants do not match the curated reaction rule.")

    expected_products = Counter(
        _canonical_smiles(_read_molecule(product["smiles"], "Rule product"))
        for product in rule["products"]
        for _ in range(product["quantity"])
    )
    actual_products = Counter(product["canonicalSmiles"] for product in products)
    if expected_products != actual_products:
        raise PlannerInputError("The generated products do not match the curated reaction rule.")

    for product in products:
        product["role"] = (
            "desired product"
            if product["canonicalSmiles"] == rule["principalProductSmiles"]
            else "coproduct"
        )
    balance = _product_balance(reactants, products)
    if not balance["atomBalanceChecked"] or not balance["chargeBalanceChecked"]:
        raise PlannerInputError("A reaction failed its independent atom/charge-balance check.")
    return {
        "step": step_number,
        "reactionId": rule["id"],
        "name": rule["name"],
        "family": rule["family"],
        "conditions": rule["conditions"],
        "shortDescription": rule["shortDescription"],
        "safetyNotes": rule["safetyNotes"],
        "stoichiometry": rule["stoichiometry"],
        "explanation": (
            "A nucleophile attacks the acyl carbon; collapse of the tetrahedral intermediate "
            "replaces chloride. The specified proton transfer and every coproduct atom are "
            "explicitly represented in the product graph."
        ),
        "reactants": [
            {
                "canonicalSmiles": _canonical_smiles(Chem.RemoveHs(molecule)),
                "formula": rdMolDescriptors.CalcMolFormula(Chem.RemoveHs(molecule)),
                "atoms": [
                    {"element": atom.GetSymbol(), "origin": _origin(atom)}
                    for atom in molecule.GetAtoms()
                ],
            }
            for molecule in reactants
        ],
        "products": products,
        "bondChanges": changes,
        "validation": {
            **balance,
            "productGraphsSanitized": True,
            "atomProvenanceComplete": all(
                "origin" in atom for product in products for atom in product["atoms"]
            ),
            "atomIndexMeaning": "Heavy-atom indices are zero-based in the canonical source SMILES graph; hydrogens are identified by their parent atom and per-parent ordinal.",
            "reactionFeasibility": "Limited to this exact curated exemplar and its documented conditions.",
        },
        "evidence": {
            "classification": rule["classification"],
            "referenceIds": rule["referenceIds"],
            "limitations": rule["limitations"],
        },
    }


def _search(
    starting_materials: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    ammonia_equivalents: int,
) -> dict[str, Any]:
    inventory: dict[tuple[str, str, str], int] = {}
    for material in starting_materials:
        key = (
            material["canonicalSmiles"],
            material["id"],
            material.get("name") or material["formula"],
        )
        inventory[key] = inventory.get(key, 0) + material["quantity"]

    queue = deque([(inventory, ammonia_equivalents, [])])
    visited = {_inventory_signature(inventory, ammonia_equivalents)}
    expanded = 0
    while queue and expanded < MAX_SEARCH_STATES:
        current_inventory, available_ammonia, steps = queue.popleft()
        if _is_goal(current_inventory, targets):
            return {
                "status": "route-found",
                "route": steps,
                "search": {
                    "algorithm": "breadth-first forward search over finite supplied inventory",
                    "objective": "minimum number of curated reaction steps",
                    "maxDepth": MAX_SEARCH_DEPTH,
                    "maxExpandedStates": MAX_SEARCH_STATES,
                    "expandedStates": expanded,
                    "complete": True,
                },
            }
        if len(steps) >= MAX_SEARCH_DEPTH:
            continue
        expanded += 1

        acid_key = _find_lot(current_inventory, "CC(=O)Cl")
        if acid_key is None:
            continue
        acid_material = {
            "canonicalSmiles": acid_key[0],
            "sourceId": acid_key[1],
            "sourceName": acid_key[2],
        }

        if available_ammonia >= 2 and _target_is_still_required(
            current_inventory, targets, RULES[0]["principalProductSmiles"]
        ):
            rule = RULES[0]
            products, changes, reactants = _run_ammonolysis(
                acid_material, ammonia_equivalents - available_ammonia + 1
            )
            next_inventory = current_inventory.copy()
            next_inventory[acid_key] -= 1
            step = _route_step(rule, products, changes, reactants, len(steps) + 1)
            _add_products_to_inventory(next_inventory, products, len(steps) + 1)
            next_ammonia = available_ammonia - 2
            signature = _inventory_signature(next_inventory, next_ammonia)
            if signature not in visited:
                visited.add(signature)
                queue.append((next_inventory, next_ammonia, [*steps, step]))

        ethanol_key = _find_lot(current_inventory, "CCO")
        if ethanol_key is not None and _target_is_still_required(
            current_inventory, targets, RULES[1]["principalProductSmiles"]
        ):
            rule = RULES[1]
            ethanol_material = {
                "canonicalSmiles": ethanol_key[0],
                "sourceId": ethanol_key[1],
                "sourceName": ethanol_key[2],
            }
            products, changes, reactants = _run_ethanolysis(
                acid_material, ethanol_material
            )
            next_inventory = current_inventory.copy()
            next_inventory[acid_key] -= 1
            next_inventory[ethanol_key] -= 1
            step = _route_step(rule, products, changes, reactants, len(steps) + 1)
            _add_products_to_inventory(next_inventory, products, len(steps) + 1)
            signature = _inventory_signature(next_inventory, available_ammonia)
            if signature not in visited:
                visited.add(signature)
                queue.append((next_inventory, available_ammonia, [*steps, step]))

    complete = not queue
    return {
        "status": "no-supported-route" if complete else "search-limit-reached",
        "route": [],
        "search": {
            "algorithm": "breadth-first forward search over finite supplied inventory",
            "objective": "minimum number of curated reaction steps",
            "maxDepth": MAX_SEARCH_DEPTH,
            "maxExpandedStates": MAX_SEARCH_STATES,
            "expandedStates": expanded,
            "complete": complete,
        },
        "message": (
            f"No route was found within the documented reaction subset, {MAX_SEARCH_DEPTH}-step depth limit, "
            "and finite supplied inventory. This does not establish that the target is chemically "
            "unreachable by other reactions."
            if complete
            else "The search reached its configured state limit; no conclusion about route existence is available."
        ),
    }


def plan_synthesis(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise PlannerInputError("The JSON request body must be an object.")
    starting_materials = _compound_entries(
        payload, "startingMaterials", must_be_organic=True
    )
    targets = _compound_entries(payload, "targetProducts", must_be_organic=True)
    reagent_mode = payload.get("reagentMode", "manual")
    if not isinstance(reagent_mode, str) or reagent_mode not in {"manual", "auto"}:
        raise PlannerInputError("reagentMode must be 'manual' or 'auto'.")
    reagents = _reagent_inventory(payload)
    if reagent_mode == "auto":
        available_acid_chloride = sum(
            item["quantity"]
            for item in starting_materials
            if item["canonicalSmiles"] == "CC(=O)Cl"
        )
        starting_acetamide = sum(
            item["quantity"]
            for item in starting_materials
            if item["canonicalSmiles"] == RULES[0]["principalProductSmiles"]
        )
        required_acetamide = sum(
            item["quantity"]
            for item in targets
            if item["canonicalSmiles"] == RULES[0]["principalProductSmiles"]
        )
        ammonia_needed = max(0, required_acetamide - starting_acetamide) * 2
        reagents["ammonia"] = min(available_acid_chloride * 2, ammonia_needed)
    result = _search(starting_materials, targets, reagents["ammonia"])
    result.update(
        {
            "knowledgeBase": {
                "name": "AtomView curated organic reaction exemplars",
                "rules": [
                    {
                        "id": rule["id"],
                        "name": rule["name"],
                        "classification": rule["classification"],
                    }
                    for rule in RULES
                ],
                "notComprehensive": True,
            },
            "startingMaterials": starting_materials,
            "targetProducts": targets,
            "authorizedReagents": [
                {"name": "ammonia", "formula": "NH3", "quantity": reagents["ammonia"]}
            ] if reagents["ammonia"] else [],
            "reagentMode": reagent_mode,
            "interpretation": (
                "A route is a graph-valid, atom- and charge-balanced application of a narrowly "
                "scoped, evidence-listed rule. It is not a yield, kinetic, thermodynamic, or "
                "experimental-success prediction."
            ),
        }
    )
    return result


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        self._send_json(
            200,
            {
                "status": "ready",
                "engine": "AtomView curated forward synthesis search",
                "reactionRules": [
                    {"id": rule["id"], "name": rule["name"]}
                    for rule in RULES
                ],
                "limits": {
                    "maxDepth": MAX_SEARCH_DEPTH,
                    "maxExpandedStates": MAX_SEARCH_STATES,
                },
            },
        )

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length header."})
            return
        if content_length <= 0:
            self._send_json(400, {"error": "A JSON request body is required."})
            return
        if content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Request body exceeds the 1 MB limit."})
            return
        try:
            payload = json.loads(self.rfile.read(content_length))
            self._send_json(200, plan_synthesis(payload))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            self._send_json(400, {"error": f"Invalid JSON request: {error}"})
        except (PlannerInputError, GeometryInputError) as error:
            self._send_json(422, {"error": str(error)})
        except Exception as error:
            print(f"Reaction planning failed: {error!r}")
            self._send_json(500, {"error": "Reaction planning failed unexpectedly."})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"Reaction planner API: {format % args}")
