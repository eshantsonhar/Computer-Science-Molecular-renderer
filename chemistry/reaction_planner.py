import heapq
import hashlib
import itertools
import json
import logging
import os
import time
import uuid
from collections import Counter
from http.server import BaseHTTPRequestHandler
from typing import Any

from api.geometry import GeometryInputError, MAX_HEAVY_ATOMS
from api.molecule_depiction import render_2d_svg
from api.structure_naming import name_structure
from chemistry.reaction_catalog import REAGENT_CATALOGUE, REFERENCES, RULES
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors


MAX_REQUEST_BYTES = 1_000_000
MAX_MATERIAL_ENTRIES = 20
MAX_SEARCH_DEPTH = 20
MAX_SEARCH_STATES = 1_000
InventoryKey = tuple[str, str, str, str]

_LOGGER = logging.getLogger(__name__)


def _catalogue_version() -> str:
    """Return a stable, non-secret identifier for the effective rule catalogue."""
    catalogue = {
        "reactionRules": RULES,
        "reagentCatalogue": REAGENT_CATALOGUE,
    }
    serialized = json.dumps(catalogue, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def _build_identity() -> dict[str, str | None]:
    commit = os.environ.get("VERCEL_GIT_COMMIT_SHA")
    if not commit or not all(character in "0123456789abcdefABCDEF" for character in commit):
        commit = None
    return {
        "commit": commit,
        "build": os.environ.get("VERCEL_DEPLOYMENT_ID")
        or os.environ.get("VERCEL_URL"),
        "catalogue": _catalogue_version(),
    }


class PlannerInputError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "invalid_request",
        kind: str = "user-input",
    ):
        super().__init__(message)
        self.code = code
        self.kind = kind


def _read_molecule(smiles: Any, label: str) -> Chem.Mol:
    if not isinstance(smiles, str) or not smiles.strip() or len(smiles) > 2_000:
        raise PlannerInputError(f"{label} must contain a SMILES string of at most 2,000 characters.")
    molecule = Chem.MolFromSmiles(smiles.strip(), sanitize=True)
    if molecule is None or molecule.GetNumAtoms() == 0:
        raise PlannerInputError(
            f"{label} is not a valid, sanitizable molecular structure.",
            code="invalid_structure",
            kind="invalid-structure",
        )
    if molecule.GetNumHeavyAtoms() > MAX_HEAVY_ATOMS:
        raise PlannerInputError(
            f"{label} exceeds the {MAX_HEAVY_ATOMS}-heavy-atom planner limit.",
            code="structure_limit_exceeded",
            kind="invalid-structure",
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
        "depictionSvg": render_2d_svg(molecule),
        **name_structure(molecule),
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
        result["providedName"] = name
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
            raise PlannerInputError(
                f"{key} entries must contain at least one carbon atom.",
                code="invalid_structure",
                kind="invalid-structure",
            )
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


def _reagent_inventory(payload: Any) -> dict[str, int | None]:
    if "reagentIds" in payload:
        reagent_ids = payload["reagentIds"]
        if not isinstance(reagent_ids, list) or any(
            not isinstance(reagent_id, str) for reagent_id in reagent_ids
        ):
            raise PlannerInputError("reagentIds must be an array of reagent identifiers.")
        if len(reagent_ids) != len(set(reagent_ids)):
            raise PlannerInputError("reagentIds must not contain duplicates.")
        unsupported = set(reagent_ids) - set(REAGENT_CATALOGUE)
        if unsupported:
            raise PlannerInputError(
                "Unsupported reagent identifiers: " + ", ".join(sorted(unsupported)) + "."
            )
        return {reagent_id: None for reagent_id in reagent_ids}

    reagents = payload.get("reagents", {})
    if not isinstance(reagents, dict):
        raise PlannerInputError("reagents must be an object or reagentIds must be an array.")
    unsupported = set(reagents) - set(REAGENT_CATALOGUE)
    if unsupported:
        raise PlannerInputError(
            "Unsupported reagent inventory: " + ", ".join(sorted(unsupported)) + "."
        )
    inventory: dict[str, int | None] = {}
    for reagent_id, quantity in reagents.items():
        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or not 0 <= quantity <= 100
        ):
            raise PlannerInputError(
                f"reagents.{reagent_id} must be an integer from 0 to 100 equivalents."
            )
        if quantity:
            inventory[reagent_id] = quantity
    return inventory


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


def _carbonyl_centres(molecule: Chem.Mol) -> list[tuple[int, int]]:
    centres = []
    for atom in molecule.GetAtoms():
        if atom.GetAtomicNum() != 6:
            continue
        oxygen = next(
            (
                bond.GetOtherAtomIdx(atom.GetIdx())
                for bond in atom.GetBonds()
                if bond.GetBondType() == Chem.BondType.DOUBLE
                and bond.GetOtherAtom(atom).GetAtomicNum() == 8
            ),
            None,
        )
        if oxygen is not None:
            centres.append((atom.GetIdx(), oxygen))
    return centres


def _acyl_chloride_sites(molecule: Chem.Mol) -> list[dict[str, int]]:
    sites = []
    for carbon, oxygen in _carbonyl_centres(molecule):
        chlorine = next(
            (
                neighbor.GetIdx()
                for neighbor in molecule.GetAtomWithIdx(carbon).GetNeighbors()
                if neighbor.GetAtomicNum() == 17
                and molecule.GetBondBetweenAtoms(carbon, neighbor.GetIdx()).GetBondType()
                == Chem.BondType.SINGLE
            ),
            None,
        )
        if chlorine is not None:
            sites.append({"carbon": carbon, "oxygen": oxygen, "leaving": chlorine})
    return sites


def _acid_sites(molecule: Chem.Mol) -> list[dict[str, int]]:
    sites = []
    for carbon, oxygen in _carbonyl_centres(molecule):
        hydroxyl = next(
            (
                neighbor.GetIdx()
                for neighbor in molecule.GetAtomWithIdx(carbon).GetNeighbors()
                if neighbor.GetAtomicNum() == 8
                and molecule.GetBondBetweenAtoms(carbon, neighbor.GetIdx()).GetBondType()
                == Chem.BondType.SINGLE
                and neighbor.GetTotalNumHs(includeNeighbors=True) == 1
            ),
            None,
        )
        if hydroxyl is not None:
            sites.append({"carbon": carbon, "oxygen": oxygen, "hydroxyl": hydroxyl})
    return sites


def _carboxylate_sites(molecule: Chem.Mol) -> list[dict[str, int]]:
    sites = []
    for carbon, oxygen in _carbonyl_centres(molecule):
        anionic_oxygen = next(
            (
                neighbor.GetIdx()
                for neighbor in molecule.GetAtomWithIdx(carbon).GetNeighbors()
                if neighbor.GetAtomicNum() == 8
                and neighbor.GetFormalCharge() == -1
                and molecule.GetBondBetweenAtoms(carbon, neighbor.GetIdx()).GetBondType()
                == Chem.BondType.SINGLE
            ),
            None,
        )
        if anionic_oxygen is not None:
            sites.append({"carbon": carbon, "oxygen": oxygen, "anionic": anionic_oxygen})
    return sites


def _ester_sites(molecule: Chem.Mol) -> list[dict[str, int]]:
    sites = []
    for carbon, carbonyl_oxygen in _carbonyl_centres(molecule):
        alkoxy_oxygen = next(
            (
                neighbor.GetIdx()
                for neighbor in molecule.GetAtomWithIdx(carbon).GetNeighbors()
                if neighbor.GetAtomicNum() == 8
                and molecule.GetBondBetweenAtoms(carbon, neighbor.GetIdx()).GetBondType()
                == Chem.BondType.SINGLE
                and any(
                    adjacent.GetAtomicNum() == 6
                    and adjacent.GetIdx() != carbon
                    for adjacent in neighbor.GetNeighbors()
                )
            ),
            None,
        )
        if alkoxy_oxygen is None:
            continue
        alkyl_carbon = next(
            neighbor.GetIdx()
            for neighbor in molecule.GetAtomWithIdx(alkoxy_oxygen).GetNeighbors()
            if neighbor.GetAtomicNum() == 6 and neighbor.GetIdx() != carbon
        )
        sites.append(
            {
                "carbon": carbon,
                "carbonylOxygen": carbonyl_oxygen,
                "alkoxyOxygen": alkoxy_oxygen,
                "alkylCarbon": alkyl_carbon,
            }
        )
    return sites


def _simple_hydrocarbon(molecule: Chem.Mol) -> bool:
    return all(atom.GetAtomicNum() == 6 for atom in molecule.GetAtoms()) and not any(
        atom.GetIsAromatic() for atom in molecule.GetAtoms()
    )


def _unsaturated_bonds(
    molecule: Chem.Mol, bond_type: Chem.BondType
) -> list[tuple[int, int]]:
    return [
        (bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
        for bond in molecule.GetBonds()
        if bond.GetBondType() == bond_type
        and bond.GetBeginAtom().GetAtomicNum() == 6
        and bond.GetEndAtom().GetAtomicNum() == 6
        and not bond.GetIsAromatic()
    ]


def _is_linear_hydrocarbon(molecule: Chem.Mol, bond_type: Chem.BondType) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if not _simple_hydrocarbon(molecule) or len(Chem.GetMolFrags(molecule)) != 1:
        return False
    unsaturated = _unsaturated_bonds(molecule, bond_type)
    if len(unsaturated) != 1:
        return False
    if any(atom.IsInRing() or atom.GetDegree() > 2 for atom in molecule.GetAtoms()):
        return False
    return all(
        bond.GetBondType() in {Chem.BondType.SINGLE, bond_type}
        for bond in molecule.GetBonds()
    )


def _is_simple_acyl_chloride(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    sites = _acyl_chloride_sites(molecule)
    if len(sites) != 1:
        return False
    if sum(atom.GetAtomicNum() == 8 for atom in molecule.GetAtoms()) != 1:
        return False
    if sum(atom.GetAtomicNum() == 17 for atom in molecule.GetAtoms()) != 1:
        return False
    return all(atom.GetAtomicNum() in {6, 8, 17} for atom in molecule.GetAtoms())


def _is_simple_carboxylic_acid(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if len(_acid_sites(molecule)) != 1:
        return False
    return (
        sum(atom.GetAtomicNum() == 8 for atom in molecule.GetAtoms()) == 2
        and all(atom.GetAtomicNum() in {6, 8} for atom in molecule.GetAtoms())
    )


def _is_single_carboxylate(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    return len(_carboxylate_sites(molecule)) == 1


def _is_primary_or_secondary_amine(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if not all(
        atom.GetAtomicNum() in {6, 7} and not atom.GetIsAromatic()
        for atom in molecule.GetAtoms()
    ):
        return False
    nitrogens = [atom for atom in molecule.GetAtoms() if atom.GetAtomicNum() == 7]
    if len(nitrogens) != 1:
        return False
    nitrogen = nitrogens[0]
    carbon_neighbors = [
        neighbor for neighbor in nitrogen.GetNeighbors() if neighbor.GetAtomicNum() == 6
    ]
    return (
        nitrogen.GetFormalCharge() == 0
        and not nitrogen.GetIsAromatic()
        and len(carbon_neighbors) in {1, 2}
        and nitrogen.GetTotalNumHs(includeNeighbors=True) == 3 - len(carbon_neighbors)
        and all(
            not (
                neighbor.GetAtomicNum() == 6
                and any(
                    bond.GetBondType() == Chem.BondType.DOUBLE
                    and bond.GetOtherAtom(neighbor).GetAtomicNum() == 8
                    for bond in neighbor.GetBonds()
                )
            )
            for neighbor in carbon_neighbors
        )
    )


def _is_single_primary_or_secondary_alcohol(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if not all(atom.GetAtomicNum() in {6, 8} for atom in molecule.GetAtoms()):
        return False
    oxygens = [atom for atom in molecule.GetAtoms() if atom.GetAtomicNum() == 8]
    if len(oxygens) != 1 or oxygens[0].GetTotalNumHs(includeNeighbors=True) != 1:
        return False
    carbon = next(
        (neighbor for neighbor in oxygens[0].GetNeighbors() if neighbor.GetAtomicNum() == 6),
        None,
    )
    if carbon is None or carbon.GetIsAromatic() or carbon.GetHybridization() != Chem.HybridizationType.SP3:
        return False
    return sum(neighbor.GetAtomicNum() == 6 for neighbor in carbon.GetNeighbors()) <= 2


def _is_saturated_simple_carboxylic_acid(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    sites = _acid_sites(molecule)
    if not _is_simple_carboxylic_acid(molecule) or any(
        atom.GetIsAromatic() or atom.IsInRing() for atom in molecule.GetAtoms()
    ):
        return False
    carbonyl_bonds = {
        tuple(sorted((site["carbon"], site["oxygen"])))
        for site in sites
    }
    return all(
        bond.GetBondType() == Chem.BondType.SINGLE
        or (
            bond.GetBondType() == Chem.BondType.DOUBLE
            and tuple(sorted((bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())))
            in carbonyl_bonds
        )
        for bond in molecule.GetBonds()
    )


def _is_saturated_primary_or_secondary_alcohol(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    return (
        _is_single_primary_or_secondary_alcohol(molecule)
        and all(
            not atom.GetIsAromatic() and not atom.IsInRing()
            for atom in molecule.GetAtoms()
        )
        and all(bond.GetBondType() == Chem.BondType.SINGLE for bond in molecule.GetBonds())
    )


def _is_single_primary_alkyl_ester(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    sites = _ester_sites(molecule)
    if len(sites) != 1 or sum(atom.GetAtomicNum() == 8 for atom in molecule.GetAtoms()) != 2:
        return False
    if not all(atom.GetAtomicNum() in {6, 8} for atom in molecule.GetAtoms()):
        return False
    alkyl_carbon = molecule.GetAtomWithIdx(sites[0]["alkylCarbon"])
    return (
        not alkyl_carbon.GetIsAromatic()
        and alkyl_carbon.GetHybridization() == Chem.HybridizationType.SP3
        and sum(neighbor.GetAtomicNum() == 6 for neighbor in alkyl_carbon.GetNeighbors()) <= 1
    )


def _is_single_hydrocarbon_alkene(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if not _simple_hydrocarbon(molecule) or len(Chem.GetMolFrags(molecule)) != 1:
        return False
    if len(_unsaturated_bonds(molecule, Chem.BondType.DOUBLE)) != 1:
        return False
    return all(
        bond.GetBondType() in {Chem.BondType.SINGLE, Chem.BondType.DOUBLE}
        and not bond.GetIsAromatic()
        for bond in molecule.GetBonds()
    )


def _is_linear_terminal_alkene(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if not _is_linear_hydrocarbon(molecule, Chem.BondType.DOUBLE):
        return False
    carbon_a, carbon_b = _unsaturated_bonds(molecule, Chem.BondType.DOUBLE)[0]
    return any(
        sum(neighbor.GetAtomicNum() == 6 for neighbor in molecule.GetAtomWithIdx(index).GetNeighbors())
        == 1
        for index in (carbon_a, carbon_b)
    )


def _is_simple_saturated_alcohol(molecule: Chem.Mol, carbon_neighbors: set[int]) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if not all(atom.GetAtomicNum() in {6, 8} for atom in molecule.GetAtoms()):
        return False
    oxygens = [atom for atom in molecule.GetAtoms() if atom.GetAtomicNum() == 8]
    if len(oxygens) != 1 or oxygens[0].GetTotalNumHs(includeNeighbors=True) != 1:
        return False
    carbon = next(
        (neighbor for neighbor in oxygens[0].GetNeighbors() if neighbor.GetAtomicNum() == 6),
        None,
    )
    return (
        carbon is not None
        and sum(neighbor.GetAtomicNum() == 6 for neighbor in carbon.GetNeighbors())
        in carbon_neighbors
        and not any(atom.IsInRing() or atom.GetIsAromatic() for atom in molecule.GetAtoms())
        and all(bond.GetBondType() == Chem.BondType.SINGLE for bond in molecule.GetBonds())
    )


def _aldehyde_site(molecule: Chem.Mol) -> tuple[int, int] | None:
    molecule = Chem.RemoveHs(molecule)
    for carbon, oxygen in _carbonyl_centres(molecule):
        carbon_atom = molecule.GetAtomWithIdx(carbon)
        if (
            sum(neighbor.GetAtomicNum() == 6 for neighbor in carbon_atom.GetNeighbors()) == 1
            and carbon_atom.GetTotalNumHs(includeNeighbors=True) == 1
        ):
            return carbon, oxygen
    return None


def _is_simple_aliphatic_aldehyde(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    site = _aldehyde_site(molecule)
    return (
        site is not None
        and all(atom.GetAtomicNum() in {6, 8} for atom in molecule.GetAtoms())
        and sum(atom.GetAtomicNum() == 8 for atom in molecule.GetAtoms()) == 1
        and not any(atom.IsInRing() or atom.GetIsAromatic() for atom in molecule.GetAtoms())
        and all(
            bond.GetBondType() in {Chem.BondType.SINGLE, Chem.BondType.DOUBLE}
            and (
                bond.GetBondType() == Chem.BondType.SINGLE
                or bond.GetBeginAtom().GetAtomicNum() == 8
                or bond.GetEndAtom().GetAtomicNum() == 8
            )
            for bond in molecule.GetBonds()
        )
    )


def _is_single_simple_aldehyde(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    site = _aldehyde_site(molecule)
    if not (
        site is not None
        and sum(atom.GetAtomicNum() == 8 for atom in molecule.GetAtoms()) == 1
        and all(atom.GetAtomicNum() in {6, 8} for atom in molecule.GetAtoms())
        and sum(
            atom.GetAtomicNum() == 6 and atom.GetIsAromatic()
            for atom in molecule.GetAtoms()
        )
        in {0, 6}
        and len(_carbonyl_centres(molecule)) == 1
    ):
        return False
    aldehyde_bond = tuple(sorted(site))
    return all(
        bond.GetBondType() in {Chem.BondType.SINGLE, Chem.BondType.AROMATIC}
        or (
            bond.GetBondType() == Chem.BondType.DOUBLE
            and tuple(sorted((bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())))
            == aldehyde_bond
        )
        for bond in molecule.GetBonds()
    )


def _is_unsubstituted_benzene(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    return (
        molecule.GetNumAtoms() == 6
        and all(atom.GetAtomicNum() == 6 and atom.GetIsAromatic() for atom in molecule.GetAtoms())
        and sum(bond.GetIsAromatic() for bond in molecule.GetBonds()) == 6
    )


def _is_single_hydroxybenzoic_acid(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if (
        molecule.GetNumAtoms() != 10
        or sum(atom.GetAtomicNum() == 6 for atom in molecule.GetAtoms()) != 7
        or sum(atom.GetAtomicNum() == 8 for atom in molecule.GetAtoms()) != 3
        or any(atom.GetAtomicNum() not in {6, 8} for atom in molecule.GetAtoms())
        or len(_acid_sites(molecule)) != 1
    ):
        return False
    ring_atoms = [
        atom for atom in molecule.GetAtoms() if atom.GetIsAromatic() and atom.GetAtomicNum() == 6
    ]
    phenolic_oxygens = [
        atom
        for atom in molecule.GetAtoms()
        if atom.GetAtomicNum() == 8
        and atom.GetTotalNumHs(includeNeighbors=True) == 1
        and any(neighbor.GetIsAromatic() for neighbor in atom.GetNeighbors())
    ]
    acid_carbon = molecule.GetAtomWithIdx(_acid_sites(molecule)[0]["carbon"])
    return (
        len(ring_atoms) == 6
        and len(phenolic_oxygens) == 1
        and sum(neighbor.GetIsAromatic() for neighbor in acid_carbon.GetNeighbors()) == 1
        and sum(atom.IsInRing() for atom in molecule.GetAtoms()) == 6
    )


def _is_single_aminophenol(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if (
        molecule.GetNumAtoms() != 8
        or sum(atom.GetAtomicNum() == 6 for atom in molecule.GetAtoms()) != 6
        or sum(atom.GetAtomicNum() == 7 for atom in molecule.GetAtoms()) != 1
        or sum(atom.GetAtomicNum() == 8 for atom in molecule.GetAtoms()) != 1
        or any(atom.GetAtomicNum() not in {6, 7, 8} for atom in molecule.GetAtoms())
    ):
        return False
    aromatic_carbons = [
        atom for atom in molecule.GetAtoms() if atom.GetAtomicNum() == 6 and atom.GetIsAromatic()
    ]
    amines = [
        atom
        for atom in molecule.GetAtoms()
        if atom.GetAtomicNum() == 7
        and atom.GetTotalNumHs(includeNeighbors=True) == 2
        and any(neighbor.GetIsAromatic() for neighbor in atom.GetNeighbors())
    ]
    phenols = [
        atom
        for atom in molecule.GetAtoms()
        if atom.GetAtomicNum() == 8
        and atom.GetTotalNumHs(includeNeighbors=True) == 1
        and any(neighbor.GetIsAromatic() for neighbor in atom.GetNeighbors())
    ]
    return len(aromatic_carbons) == 6 and len(amines) == 1 and len(phenols) == 1


def _is_simple_phenol(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    return (
        molecule.GetNumAtoms() == 7
        and sum(atom.GetAtomicNum() == 6 and atom.GetIsAromatic() for atom in molecule.GetAtoms()) == 6
        and sum(
            atom.GetAtomicNum() == 8
            and atom.GetTotalNumHs(includeNeighbors=True) == 1
            and any(neighbor.GetIsAromatic() for neighbor in atom.GetNeighbors())
            for atom in molecule.GetAtoms()
        )
        == 1
    )


def _is_simple_phenoxide(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    return (
        molecule.GetNumAtoms() == 7
        and sum(atom.GetAtomicNum() == 6 and atom.GetIsAromatic() for atom in molecule.GetAtoms()) == 6
        and sum(
            atom.GetAtomicNum() == 8
            and atom.GetFormalCharge() == -1
            and any(neighbor.GetIsAromatic() for neighbor in atom.GetNeighbors())
            for atom in molecule.GetAtoms()
        )
        == 1
    )


def _is_carbon_dioxide(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    return (
        molecule.GetNumAtoms() == 3
        and sum(atom.GetAtomicNum() == 6 for atom in molecule.GetAtoms()) == 1
        and sum(atom.GetAtomicNum() == 8 for atom in molecule.GetAtoms()) == 2
        and len(_carbonyl_centres(molecule)) == 1
        and all(bond.GetBondType() == Chem.BondType.DOUBLE for bond in molecule.GetBonds())
    )


def _is_ammonia(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    return molecule.GetNumAtoms() == 1 and molecule.GetAtomWithIdx(0).GetAtomicNum() == 7


def _is_hydrogen_cyanide(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    return (
        molecule.GetNumAtoms() == 2
        and sorted(atom.GetAtomicNum() for atom in molecule.GetAtoms()) == [6, 7]
        and any(bond.GetBondType() == Chem.BondType.TRIPLE for bond in molecule.GetBonds())
    )


def _is_simple_imine(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if not all(atom.GetAtomicNum() in {6, 7} for atom in molecule.GetAtoms()):
        return False
    imines = [
        bond
        for bond in molecule.GetBonds()
        if bond.GetBondType() == Chem.BondType.DOUBLE
        and {bond.GetBeginAtom().GetAtomicNum(), bond.GetEndAtom().GetAtomicNum()} == {6, 7}
    ]
    if len(imines) != 1:
        return False
    carbon = next(atom for atom in (imines[0].GetBeginAtom(), imines[0].GetEndAtom()) if atom.GetAtomicNum() == 6)
    nitrogen = imines[0].GetOtherAtom(carbon)
    return (
        sum(neighbor.GetAtomicNum() == 6 for neighbor in carbon.GetNeighbors()) == 1
        and carbon.GetTotalNumHs(includeNeighbors=True) == 1
        and sum(neighbor.GetAtomicNum() == 6 for neighbor in nitrogen.GetNeighbors()) == 1
        and nitrogen.GetTotalNumHs(includeNeighbors=True) == 1
        and all(atom.GetAtomicNum() != 7 for atom in molecule.GetAtoms() if atom.GetIdx() != nitrogen.GetIdx())
        and not any(atom.IsInRing() for atom in molecule.GetAtoms())
    )


def _is_simple_alpha_aminonitrile(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if not all(atom.GetAtomicNum() in {6, 7} for atom in molecule.GetAtoms()):
        return False
    nitrile_bonds = [
        bond
        for bond in molecule.GetBonds()
        if bond.GetBondType() == Chem.BondType.TRIPLE
        and {bond.GetBeginAtom().GetAtomicNum(), bond.GetEndAtom().GetAtomicNum()} == {6, 7}
    ]
    amino_nitrogens = [
        atom
        for atom in molecule.GetAtoms()
        if atom.GetAtomicNum() == 7
        and atom.GetTotalNumHs(includeNeighbors=True) == 2
        and sum(neighbor.GetAtomicNum() == 6 for neighbor in atom.GetNeighbors()) == 1
    ]
    if len(nitrile_bonds) != 1 or len(amino_nitrogens) != 1:
        return False
    nitrile_carbon = next(
        atom
        for atom in (
            nitrile_bonds[0].GetBeginAtom(),
            nitrile_bonds[0].GetEndAtom(),
        )
        if atom.GetAtomicNum() == 6
    )
    alpha_carbon = next(
        (
            neighbor
            for neighbor in nitrile_carbon.GetNeighbors()
            if neighbor.GetAtomicNum() == 6 and neighbor.GetIdx() != nitrile_carbon.GetIdx()
        ),
        None,
    )
    amino_nitrogen = amino_nitrogens[0]
    return (
        alpha_carbon is not None
        and alpha_carbon.GetHybridization() == Chem.HybridizationType.SP3
        and any(
            neighbor.GetIdx() == alpha_carbon.GetIdx()
            for neighbor in amino_nitrogen.GetNeighbors()
        )
        and not any(atom.IsInRing() for atom in molecule.GetAtoms())
        and all(
            bond.GetBondType() in {Chem.BondType.SINGLE, Chem.BondType.TRIPLE}
            and (
                bond.GetBondType() == Chem.BondType.SINGLE
                or bond.GetIdx() == nitrile_bonds[0].GetIdx()
            )
            for bond in molecule.GetBonds()
        )
    )


def _is_butane_1_4_dial(molecule: Chem.Mol) -> bool:
    molecule = Chem.RemoveHs(molecule)
    if (
        molecule.GetNumAtoms() != 6
        or sum(atom.GetAtomicNum() == 6 for atom in molecule.GetAtoms()) != 4
        or sum(atom.GetAtomicNum() == 8 for atom in molecule.GetAtoms()) != 2
        or any(atom.GetAtomicNum() not in {6, 8} for atom in molecule.GetAtoms())
        or len(_carbonyl_centres(molecule)) != 2
        or any(atom.IsInRing() or atom.GetIsAromatic() for atom in molecule.GetAtoms())
    ):
        return False
    aldehyde_carbons = {
        carbon
        for carbon, _oxygen in _carbonyl_centres(molecule)
        if molecule.GetAtomWithIdx(carbon).GetTotalNumHs(includeNeighbors=True) == 1
        and sum(
            neighbor.GetAtomicNum() == 6
            for neighbor in molecule.GetAtomWithIdx(carbon).GetNeighbors()
        )
        == 1
    }
    if len(aldehyde_carbons) != 2:
        return False
    carbon_atoms = [
        atom for atom in molecule.GetAtoms() if atom.GetAtomicNum() == 6
    ]
    return all(
        sum(neighbor.GetAtomicNum() == 6 for neighbor in atom.GetNeighbors())
        == (1 if atom.GetIdx() in aldehyde_carbons else 2)
        for atom in carbon_atoms
    ) and all(
        bond.GetBondType() == Chem.BondType.SINGLE
        or (
            bond.GetBondType() == Chem.BondType.DOUBLE
            and bond.GetBeginAtom().GetAtomicNum() == 8
        )
        or (
            bond.GetBondType() == Chem.BondType.DOUBLE
            and bond.GetEndAtom().GetAtomicNum() == 8
        )
        for bond in molecule.GetBonds()
    )


SUBSTRATE_MATCHERS = {
    "acyl-chloride": _is_simple_acyl_chloride,
    "primary-secondary-amine": _is_primary_or_secondary_amine,
    "single-alcohol": _is_single_primary_or_secondary_alcohol,
    "single-carboxylate": _is_single_carboxylate,
    "single-carboxylic-acid": _is_simple_carboxylic_acid,
    "saturated-single-carboxylic-acid": _is_saturated_simple_carboxylic_acid,
    "single-primary-alkyl-ester": _is_single_primary_alkyl_ester,
    "saturated-single-alcohol": _is_saturated_primary_or_secondary_alcohol,
    "linear-single-alkene": lambda molecule: _is_linear_hydrocarbon(
        molecule, Chem.BondType.DOUBLE
    ),
    "linear-single-alkyne": lambda molecule: _is_linear_hydrocarbon(
        molecule, Chem.BondType.TRIPLE
    ),
    "single-hydrocarbon-alkene": _is_single_hydrocarbon_alkene,
    "linear-terminal-alkene": _is_linear_terminal_alkene,
    "single-primary-alcohol": lambda molecule: _is_simple_saturated_alcohol(molecule, {0, 1}),
    "single-secondary-alcohol": lambda molecule: _is_simple_saturated_alcohol(molecule, {2}),
    "single-simple-aldehyde": _is_single_simple_aldehyde,
    "simple-aliphatic-aldehyde": _is_simple_aliphatic_aldehyde,
    "unsubstituted-benzene": _is_unsubstituted_benzene,
    "single-hydroxybenzoic-acid": _is_single_hydroxybenzoic_acid,
    "single-aminophenol": _is_single_aminophenol,
    "simple-phenol": _is_simple_phenol,
    "simple-phenoxide": _is_simple_phenoxide,
    "carbon-dioxide": _is_carbon_dioxide,
    "ammonia": _is_ammonia,
    "hydrogen-cyanide": _is_hydrogen_cyanide,
    "simple-imine": _is_simple_imine,
    "simple-alpha-aminonitrile": _is_simple_alpha_aminonitrile,
    "butane-1,4-dial": _is_butane_1_4_dial,
}


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
        summary["_sourceMol"] = Chem.Mol(fragment)
        products.append(summary)
    return products


def _canonical_atom_origins(
    source_molecule: Chem.Mol, canonical_smiles: str
) -> list[dict[str, Any]]:
    source_heavy = Chem.RemoveHs(source_molecule)
    canonical = _read_molecule(canonical_smiles, "Reaction product")
    serialized_smiles = Chem.MolToSmiles(
        source_heavy, canonical=True, isomericSmiles=True
    )
    if serialized_smiles != canonical_smiles or not source_heavy.HasProp(
        "_smilesAtomOutputOrder"
    ):
        raise PlannerInputError(
            "A reaction product could not preserve atom provenance in canonical graph order.",
            code="invalid_reaction_rule",
            kind="internal",
        )
    output_order = json.loads(source_heavy.GetProp("_smilesAtomOutputOrder"))
    canonical_index_by_source = {
        source_index: canonical_index
        for canonical_index, source_index in enumerate(output_order)
    }
    if len(output_order) != canonical.GetNumAtoms():
        raise PlannerInputError(
            "A reaction product could not preserve atom provenance in canonical graph order.",
            code="invalid_reaction_rule",
            kind="internal",
        )

    heavy_origins = [
        _origin(source_heavy.GetAtomWithIdx(source_index))
        for source_index in output_order
    ]
    source_heavy_index_by_origin = {
        json.dumps(_origin(atom), separators=(",", ":"), sort_keys=True): atom.GetIdx()
        for atom in source_heavy.GetAtoms()
    }
    hydrogen_origins: dict[int, list[dict[str, Any]]] = {}
    for atom in source_molecule.GetAtoms():
        if atom.GetAtomicNum() != 1 or atom.GetDegree() != 1:
            continue
        parent = atom.GetNeighbors()[0]
        parent_origin = json.dumps(
            _origin(parent), separators=(",", ":"), sort_keys=True
        )
        source_parent = source_heavy_index_by_origin[parent_origin]
        canonical_parent = canonical_index_by_source[source_parent]
        hydrogen_origins.setdefault(canonical_parent, []).append(_origin(atom))
    for origins in hydrogen_origins.values():
        origins.sort(key=lambda origin: origin["hydrogenOrdinal"])

    explicit = Chem.AddHs(canonical)
    hydrogen_counts: Counter[int] = Counter()
    origins = []
    for atom in explicit.GetAtoms():
        if atom.GetAtomicNum() == 1:
            parent_index = atom.GetNeighbors()[0].GetIdx()
            hydrogen_index = hydrogen_counts[parent_index]
            parent_hydrogens = hydrogen_origins.get(parent_index, [])
            if hydrogen_index >= len(parent_hydrogens):
                raise PlannerInputError(
                    "A reaction product hydrogen could not be matched to its source.",
                    code="invalid_reaction_rule",
                    kind="internal",
                )
            origins.append(parent_hydrogens[hydrogen_index])
            hydrogen_counts[parent_index] += 1
        else:
            origins.append(heavy_origins[atom.GetIdx()])
    if any(
        hydrogen_counts[parent] != len(parent_origins)
        for parent, parent_origins in hydrogen_origins.items()
    ):
        raise PlannerInputError(
            "A reaction product lost hydrogen provenance during canonicalization.",
            code="invalid_reaction_rule",
            kind="internal",
        )
    return origins


def _explicit_material(material: dict[str, Any], unit: int = 1) -> Chem.Mol:
    source_id = material["sourceId"]
    if unit > 1:
        source_id = f"{source_id}-unit-{unit}"
    molecule = Chem.AddHs(_read_molecule(material["canonicalSmiles"], "Reaction reactant"))
    atom_origins = material.get("atomOrigins")
    if atom_origins is None:
        return _explicit_source_molecule(
            material["canonicalSmiles"],
            "startingMaterial",
            source_id,
            material["sourceName"],
        )
    if not isinstance(atom_origins, list) or len(atom_origins) != molecule.GetNumAtoms():
        raise PlannerInputError(
            "A reaction intermediate has incomplete atom provenance.",
            code="planner_state_error",
            kind="internal",
        )
    for atom, origin in zip(molecule.GetAtoms(), atom_origins):
        atom.SetProp("_atomViewOrigin", json.dumps(origin, separators=(",", ":")))
    return molecule


def _explicit_reagent(
    reagent_id: str, unit: int, step_number: int
) -> Chem.Mol:
    reagent = REAGENT_CATALOGUE[reagent_id]
    smiles = reagent["smiles"]
    if not isinstance(smiles, str):
        raise PlannerInputError(
            f"{reagent_id} is a condition and cannot be used as a stoichiometric reactant."
        )
    return _explicit_source_molecule(
        smiles,
        "reagent",
        f"{reagent_id}-step-{step_number}-equivalent-{unit}",
        reagent["name"],
    )


def _combine_reactants(
    reactants: list[Chem.Mol],
) -> tuple[Chem.RWMol, list[int]]:
    if not reactants:
        raise PlannerInputError("A reaction must contain at least one reactant.")
    offsets = []
    combined = reactants[0]
    offsets.append(0)
    for molecule in reactants[1:]:
        offsets.append(combined.GetNumAtoms())
        combined = Chem.CombineMols(combined, molecule)
    return Chem.RWMol(combined), offsets


def _global_index(offsets: list[int], molecule_index: int, atom_index: int) -> int:
    return offsets[molecule_index] + atom_index


def _hydrogen_neighbor(molecule: Chem.Mol, atom_index: int) -> int:
    hydrogen = next(
        (
            neighbor.GetIdx()
            for neighbor in molecule.GetAtomWithIdx(atom_index).GetNeighbors()
            if neighbor.GetAtomicNum() == 1
        ),
        None,
    )
    if hydrogen is None:
        raise PlannerInputError("A reaction proton transfer lacks an explicit source hydrogen.")
    return hydrogen


def _append_bond_change(
    changes: list[dict[str, Any]],
    label: str,
    graph: Chem.RWMol,
    atom_a: int,
    atom_b: int,
    **metadata: Any,
) -> None:
    changes.append(
        {
            "change": label,
            "from": _atom_ref(graph.GetAtomWithIdx(atom_a)),
            "to": _atom_ref(graph.GetAtomWithIdx(atom_b)),
            **metadata,
        }
    )


def _summarize_graph_change(
    reactants: list[Chem.Mol],
    product_graph: Chem.RWMol,
    principal_origins: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    products = _summarize_products(reactants, product_graph.GetMol())
    principal_keys = {
        (
            origin.get("sourceType"),
            origin.get("sourceId"),
            origin.get("atomIndex"),
        )
        for origin in principal_origins
    }
    principal_smiles = []
    for product in products:
        contains_principal_atom = any(
            (
                atom["origin"].get("sourceType"),
                atom["origin"].get("sourceId"),
                atom["origin"].get("atomIndex"),
            )
            in principal_keys
            for atom in product["atoms"]
        )
        if contains_principal_atom:
            principal_smiles.append(product["canonicalSmiles"])
    return products, principal_smiles


def _reactant_set(
    materials: list[dict[str, Any]],
    reagent_ids: list[str],
    reagent_counts: dict[str, int],
    step_number: int,
) -> list[Chem.Mol]:
    reactants = [_explicit_material(material) for material in materials]
    for reagent_id in reagent_ids:
        for unit in range(1, reagent_counts.get(reagent_id, 0) + 1):
            reactants.append(_explicit_reagent(reagent_id, unit, step_number))
    return reactants


def _run_acyl_substitution(
    rule: dict[str, Any],
    materials: list[dict[str, Any]],
    reagent_counts: dict[str, int],
    step_number: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, list(rule["reagents"]), rule["reagents"], step_number
    )
    graph, offsets = _combine_reactants(reactants)
    acid_sites = _acyl_chloride_sites(reactants[0])
    if len(acid_sites) != 1:
        raise PlannerInputError("The acyl-substitution rule requires one acyl chloride.")
    acyl = acid_sites[0]
    carbon = offsets[0] + acyl["carbon"]
    chloride = offsets[0] + acyl["leaving"]
    executor = rule["executor"]

    if executor == "acyl-ammonia":
        nucleophile_molecule_index = len(materials)
        base_molecule_index = nucleophile_molecule_index + 1
        donor_atomic_number = 7
        transfer_hydrogen = _hydrogen_neighbor(
            reactants[nucleophile_molecule_index],
            next(
                atom.GetIdx()
                for atom in reactants[nucleophile_molecule_index].GetAtoms()
                if atom.GetAtomicNum() == donor_atomic_number
            ),
        )
        base_nitrogen = next(
            atom.GetIdx()
            for atom in reactants[base_molecule_index].GetAtoms()
            if atom.GetAtomicNum() == 7
        )
        donor = next(
            atom.GetIdx()
            for atom in reactants[nucleophile_molecule_index].GetAtoms()
            if atom.GetAtomicNum() == donor_atomic_number
        )
        transfer_from = offsets[nucleophile_molecule_index] + donor
        transfer_to = offsets[base_molecule_index] + base_nitrogen
        transfer_hydrogen += offsets[nucleophile_molecule_index]
        graph.GetAtomWithIdx(transfer_to).SetFormalCharge(1)
        graph.GetAtomWithIdx(chloride).SetFormalCharge(-1)
    elif executor == "acyl-amine":
        nucleophile_molecule_index = 1
        base_molecule_index = 2
        donor = next(
            atom.GetIdx()
            for atom in reactants[nucleophile_molecule_index].GetAtoms()
            if atom.GetAtomicNum() == 7 and atom.GetTotalNumHs(includeNeighbors=True) > 0
        )
        base_nitrogen = next(
            atom.GetIdx()
            for atom in reactants[base_molecule_index].GetAtoms()
            if atom.GetAtomicNum() == 7
        )
        transfer_hydrogen = _hydrogen_neighbor(
            reactants[nucleophile_molecule_index], donor
        ) + offsets[nucleophile_molecule_index]
        transfer_from = offsets[nucleophile_molecule_index] + donor
        transfer_to = offsets[base_molecule_index] + base_nitrogen
        graph.GetAtomWithIdx(transfer_to).SetFormalCharge(1)
        graph.GetAtomWithIdx(chloride).SetFormalCharge(-1)
    elif executor in {"acyl-alcohol", "acyl-water"}:
        nucleophile_molecule_index = 1
        oxygen = next(
            atom.GetIdx()
            for atom in reactants[nucleophile_molecule_index].GetAtoms()
            if atom.GetAtomicNum() == 8
            and atom.GetTotalNumHs(includeNeighbors=True) > 0
        )
        transfer_hydrogen = _hydrogen_neighbor(
            reactants[nucleophile_molecule_index], oxygen
        ) + offsets[nucleophile_molecule_index]
        donor = offsets[nucleophile_molecule_index] + oxygen
        transfer_from = donor
        transfer_to = chloride
        graph.AddBond(carbon, donor, Chem.BondType.SINGLE)
        graph.RemoveBond(carbon, chloride)
        graph.RemoveBond(donor, transfer_hydrogen)
        graph.AddBond(chloride, transfer_hydrogen, Chem.BondType.SINGLE)
        changes = []
        _append_bond_change(changes, "broken", graph, carbon, chloride)
        _append_bond_change(changes, "formed", graph, carbon, donor)
        _append_bond_change(changes, "broken", graph, donor, transfer_hydrogen)
        _append_bond_change(changes, "formed", graph, chloride, transfer_hydrogen)
        principal_origin = _origin(graph.GetAtomWithIdx(carbon))
        products, principal = _summarize_graph_change(
            reactants, graph, [principal_origin]
        )
        return products, changes, reactants, principal
    elif executor == "acyl-carboxylate":
        nucleophile_molecule_index = 1
        sites = _carboxylate_sites(reactants[nucleophile_molecule_index])
        if len(sites) != 1:
            raise PlannerInputError("The acyl-substitution rule requires one carboxylate.")
        donor = offsets[nucleophile_molecule_index] + sites[0]["anionic"]
        graph.GetAtomWithIdx(donor).SetFormalCharge(0)
        graph.GetAtomWithIdx(chloride).SetFormalCharge(-1)
        graph.AddBond(carbon, donor, Chem.BondType.SINGLE)
        graph.RemoveBond(carbon, chloride)
        changes = []
        _append_bond_change(changes, "broken", graph, carbon, chloride)
        _append_bond_change(changes, "formed", graph, carbon, donor)
        principal_origin = _origin(graph.GetAtomWithIdx(carbon))
        products, principal = _summarize_graph_change(
            reactants, graph, [principal_origin]
        )
        return products, changes, reactants, principal
    else:
        raise PlannerInputError(f"Unknown acyl substitution executor {executor!r}.")

    graph.AddBond(carbon, transfer_from, Chem.BondType.SINGLE)
    graph.RemoveBond(carbon, chloride)
    graph.RemoveBond(transfer_from, transfer_hydrogen)
    graph.AddBond(transfer_to, transfer_hydrogen, Chem.BondType.SINGLE)
    changes = []
    _append_bond_change(changes, "broken", graph, carbon, chloride)
    _append_bond_change(changes, "formed", graph, carbon, transfer_from)
    _append_bond_change(changes, "broken", graph, transfer_from, transfer_hydrogen)
    _append_bond_change(changes, "formed", graph, transfer_to, transfer_hydrogen)
    principal_origin = _origin(graph.GetAtomWithIdx(carbon))
    products, principal = _summarize_graph_change(
        reactants, graph, [principal_origin]
    )
    return products, changes, reactants, principal


def _run_acid_chloride_formation(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, ["thionyl-chloride"], reagent_counts, step_number
    )
    acid = reactants[0]
    thionyl = reactants[1]
    acid_sites = _acid_sites(acid)
    sulfur = next(
        (atom.GetIdx() for atom in thionyl.GetAtoms() if atom.GetAtomicNum() == 16),
        None,
    )
    if len(acid_sites) != 1 or sulfur is None:
        raise PlannerInputError("Acid chloride formation requires one acid and thionyl chloride.")
    sulfur_oxygen = next(
        bond.GetOtherAtomIdx(sulfur)
        for bond in thionyl.GetAtomWithIdx(sulfur).GetBonds()
        if bond.GetOtherAtom(thionyl.GetAtomWithIdx(sulfur)).GetAtomicNum() == 8
        and bond.GetBondType() == Chem.BondType.DOUBLE
    )
    chlorides = [
        atom.GetIdx()
        for atom in thionyl.GetAtomWithIdx(sulfur).GetNeighbors()
        if atom.GetAtomicNum() == 17
    ]
    if len(chlorides) != 2:
        raise PlannerInputError("Thionyl chloride must contain two chlorine atoms.")

    graph, offsets = _combine_reactants(reactants)
    acid_offset, thionyl_offset = offsets
    site = acid_sites[0]
    carbon = acid_offset + site["carbon"]
    hydroxyl = acid_offset + site["hydroxyl"]
    proton = _hydrogen_neighbor(acid, site["hydroxyl"]) + acid_offset
    sulfur_index = sulfur + thionyl_offset
    acid_oxygen = hydroxyl
    sulfur_oxygen_index = sulfur_oxygen + thionyl_offset
    acyl_chloride = chlorides[0] + thionyl_offset
    hydrogen_chloride = chlorides[1] + thionyl_offset

    changes = []
    _append_bond_change(changes, "broken", graph, carbon, hydroxyl)
    _append_bond_change(changes, "formed", graph, carbon, acyl_chloride)
    _append_bond_change(changes, "broken", graph, sulfur_index, acyl_chloride)
    _append_bond_change(changes, "broken", graph, sulfur_index, hydrogen_chloride)
    _append_bond_change(changes, "broken", graph, hydroxyl, proton)
    _append_bond_change(changes, "formed", graph, sulfur_index, acid_oxygen)
    _append_bond_change(changes, "formed", graph, hydrogen_chloride, proton)
    graph.RemoveBond(carbon, hydroxyl)
    graph.AddBond(carbon, acyl_chloride, Chem.BondType.SINGLE)
    graph.RemoveBond(sulfur_index, acyl_chloride)
    graph.RemoveBond(sulfur_index, hydrogen_chloride)
    graph.RemoveBond(hydroxyl, proton)
    graph.AddBond(sulfur_index, acid_oxygen, Chem.BondType.DOUBLE)
    graph.AddBond(hydrogen_chloride, proton, Chem.BondType.SINGLE)
    principal_origin = _origin(graph.GetAtomWithIdx(carbon))
    products, principal = _summarize_graph_change(
        reactants, graph, [principal_origin]
    )
    return products, changes, reactants, principal


def _run_ester_saponification(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, ["sodium-hydroxide"], reagent_counts, step_number
    )
    ester = reactants[0]
    sites = _ester_sites(ester)
    hydroxide = next(
        atom.GetIdx()
        for atom in reactants[1].GetAtoms()
        if atom.GetAtomicNum() == 8 and atom.GetFormalCharge() == -1
    )
    if len(sites) != 1:
        raise PlannerInputError("Ester hydrolysis requires one ester group.")
    graph, offsets = _combine_reactants(reactants)
    ester_offset, hydroxide_offset = offsets
    site = sites[0]
    carbon = ester_offset + site["carbon"]
    alkoxy = ester_offset + site["alkoxyOxygen"]
    hydroxide_oxygen = hydroxide + hydroxide_offset
    hydroxide_hydrogen = _hydrogen_neighbor(reactants[1], hydroxide) + hydroxide_offset
    transferred_hydrogen = hydroxide_hydrogen
    principal_origin = _origin(graph.GetAtomWithIdx(carbon))
    changes = []
    _append_bond_change(changes, "broken", graph, carbon, alkoxy)
    _append_bond_change(changes, "formed", graph, carbon, hydroxide_oxygen)
    _append_bond_change(changes, "broken", graph, hydroxide_oxygen, transferred_hydrogen)
    _append_bond_change(changes, "formed", graph, alkoxy, transferred_hydrogen)
    graph.RemoveBond(carbon, alkoxy)
    graph.AddBond(carbon, hydroxide_oxygen, Chem.BondType.SINGLE)
    graph.RemoveBond(hydroxide_oxygen, transferred_hydrogen)
    graph.AddBond(alkoxy, transferred_hydrogen, Chem.BondType.SINGLE)
    graph.GetAtomWithIdx(hydroxide_oxygen).SetFormalCharge(-1)
    products, principal = _summarize_graph_change(
        reactants, graph, [principal_origin]
    )
    return products, changes, reactants, principal


def _run_fischer_esterification(
    materials: list[dict[str, Any]],
    _reagent_counts: dict[str, int],
    step_number: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(materials, [], _reagent_counts, step_number)
    graph, offsets = _combine_reactants(reactants)
    sites = _acid_sites(reactants[0])
    if len(sites) != 1:
        raise PlannerInputError("Fischer esterification requires one carboxylic acid.")
    acid = sites[0]
    carbon = offsets[0] + acid["carbon"]
    acid_hydroxyl = offsets[0] + acid["hydroxyl"]
    alcohol_oxygen = next(
        (
            atom.GetIdx()
            for atom in reactants[1].GetAtoms()
            if atom.GetAtomicNum() == 8
            and atom.GetTotalNumHs(includeNeighbors=True) == 1
        ),
        None,
    )
    if alcohol_oxygen is None:
        raise PlannerInputError("Fischer esterification requires one alcohol O-H bond.")
    alcohol_oxygen += offsets[1]
    alcohol_hydrogen = _hydrogen_neighbor(graph, alcohol_oxygen)

    graph.AddBond(carbon, alcohol_oxygen, Chem.BondType.SINGLE)
    graph.RemoveBond(carbon, acid_hydroxyl)
    graph.RemoveBond(alcohol_oxygen, alcohol_hydrogen)
    graph.AddBond(acid_hydroxyl, alcohol_hydrogen, Chem.BondType.SINGLE)

    changes = []
    _append_bond_change(changes, "formed", graph, carbon, alcohol_oxygen)
    _append_bond_change(changes, "broken", graph, carbon, acid_hydroxyl)
    _append_bond_change(changes, "broken", graph, alcohol_oxygen, alcohol_hydrogen)
    _append_bond_change(changes, "formed", graph, acid_hydroxyl, alcohol_hydrogen)
    principal_origin = _origin(graph.GetAtomWithIdx(carbon))
    products, principal = _summarize_graph_change(
        reactants, graph, [principal_origin]
    )
    return products, changes, reactants, principal


def _run_carboxylate_acidification(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, ["hydrogen-chloride"], reagent_counts, step_number
    )
    carboxylate = reactants[0]
    acid_sites = _carboxylate_sites(carboxylate)
    if len(acid_sites) != 1:
        raise PlannerInputError("Acidification requires one carboxylate group.")
    chlorine = next(
        atom.GetIdx()
        for atom in reactants[1].GetAtoms()
        if atom.GetAtomicNum() == 17
    )
    hydrogen = _hydrogen_neighbor(reactants[1], chlorine)
    graph, offsets = _combine_reactants(reactants)
    carboxylate_offset, hcl_offset = offsets
    oxygen = carboxylate_offset + acid_sites[0]["anionic"]
    chlorine += hcl_offset
    hydrogen += hcl_offset
    graph.GetAtomWithIdx(oxygen).SetFormalCharge(0)
    graph.GetAtomWithIdx(chlorine).SetFormalCharge(-1)
    principal_origin = _origin(
        graph.GetAtomWithIdx(carboxylate_offset + acid_sites[0]["carbon"])
    )
    changes = []
    _append_bond_change(changes, "broken", graph, chlorine, hydrogen)
    _append_bond_change(changes, "formed", graph, oxygen, hydrogen)
    graph.RemoveBond(chlorine, hydrogen)
    graph.AddBond(oxygen, hydrogen, Chem.BondType.SINGLE)
    products, principal = _summarize_graph_change(
        reactants, graph, [principal_origin]
    )
    return products, changes, reactants, principal


def _run_hydrogenation(
    rule: dict[str, Any],
    materials: list[dict[str, Any]],
    reagent_counts: dict[str, int],
    step_number: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(materials, ["hydrogen"], reagent_counts, step_number)
    substrate = reactants[0]
    bond_type = (
        Chem.BondType.TRIPLE
        if rule["executor"] == "hydrogenation-alkyne"
        else Chem.BondType.DOUBLE
    )
    bonds = _unsaturated_bonds(substrate, bond_type)
    if len(bonds) != 1:
        raise PlannerInputError("Hydrogenation requires one supported carbon-carbon multiple bond.")
    graph, offsets = _combine_reactants(reactants)
    substrate_offset = offsets[0]
    atom_a, atom_b = bonds[0]
    atom_a += substrate_offset
    atom_b += substrate_offset
    bond = graph.GetBondBetweenAtoms(atom_a, atom_b)
    if bond is None:
        raise PlannerInputError("The hydrogenation bond is missing from the combined reactant graph.")
    principal_origin = _origin(graph.GetAtomWithIdx(atom_a))
    changes = [
        {
            "change": "bond order changed",
            "from": _atom_ref(graph.GetAtomWithIdx(atom_a)),
            "to": _atom_ref(graph.GetAtomWithIdx(atom_b)),
            "fromBondOrder": 3 if bond_type == Chem.BondType.TRIPLE else 2,
            "toBondOrder": 1,
        }
    ]
    graph.GetBondBetweenAtoms(atom_a, atom_b).SetBondType(Chem.BondType.SINGLE)
    hydrogen_molecules = reactants[1:]
    for hydrogen_index, hydrogen_molecule in enumerate(hydrogen_molecules):
        hydrogen_atoms = [
            atom.GetIdx()
            for atom in hydrogen_molecule.GetAtoms()
            if atom.GetAtomicNum() == 1
        ]
        if len(hydrogen_atoms) != 2:
            raise PlannerInputError("Hydrogenation requires explicit dihydrogen molecules.")
        left_hydrogen = offsets[hydrogen_index + 1] + hydrogen_atoms[0]
        right_hydrogen = offsets[hydrogen_index + 1] + hydrogen_atoms[1]
        _append_bond_change(
            changes,
            "broken",
            graph,
            left_hydrogen,
            right_hydrogen,
        )
        _append_bond_change(changes, "formed", graph, atom_a, left_hydrogen)
        _append_bond_change(changes, "formed", graph, atom_b, right_hydrogen)
        graph.RemoveBond(left_hydrogen, right_hydrogen)
        graph.AddBond(atom_a, left_hydrogen, Chem.BondType.SINGLE)
        graph.AddBond(atom_b, right_hydrogen, Chem.BondType.SINGLE)
    products, principal = _summarize_graph_change(
        reactants, graph, [principal_origin]
    )
    return products, changes, reactants, principal


def _run_ozonolysis(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, ["ozone", "dimethyl-sulfide"], reagent_counts, step_number
    )
    alkene = reactants[0]
    double_bonds = _unsaturated_bonds(alkene, Chem.BondType.DOUBLE)
    ozone_oxygens = [
        atom.GetIdx() for atom in reactants[1].GetAtoms() if atom.GetAtomicNum() == 8
    ]
    sulfur = next(
        atom.GetIdx()
        for atom in reactants[2].GetAtoms()
        if atom.GetAtomicNum() == 16
    )
    if len(double_bonds) != 1 or len(ozone_oxygens) != 3:
        raise PlannerInputError("Ozonolysis requires one alkene and one ozone molecule.")
    graph, offsets = _combine_reactants(reactants)
    alkene_offset, ozone_offset, sulfide_offset = offsets
    carbon_a, carbon_b = (
        atom_index + alkene_offset for atom_index in double_bonds[0]
    )
    oxygen_a, oxygen_b, oxygen_sulfide = (
        atom_index + ozone_offset for atom_index in ozone_oxygens
    )
    sulfur_index = sulfur + sulfide_offset
    principal_origins = [
        _origin(graph.GetAtomWithIdx(carbon_a)),
        _origin(graph.GetAtomWithIdx(carbon_b)),
    ]
    changes = []
    _append_bond_change(changes, "broken", graph, carbon_a, carbon_b)
    _append_bond_change(changes, "formed", graph, carbon_a, oxygen_a)
    _append_bond_change(changes, "formed", graph, carbon_b, oxygen_b)
    _append_bond_change(changes, "formed", graph, sulfur_index, oxygen_sulfide)
    graph.RemoveBond(carbon_a, carbon_b)
    for first, second in (
        (oxygen_a, oxygen_b),
        (oxygen_b, oxygen_sulfide),
    ):
        _append_bond_change(changes, "broken", graph, first, second)
        graph.RemoveBond(first, second)
    graph.AddBond(carbon_a, oxygen_a, Chem.BondType.DOUBLE)
    graph.AddBond(carbon_b, oxygen_b, Chem.BondType.DOUBLE)
    graph.AddBond(sulfur_index, oxygen_sulfide, Chem.BondType.DOUBLE)
    for oxygen in (oxygen_a, oxygen_b, oxygen_sulfide):
        graph.GetAtomWithIdx(oxygen).SetFormalCharge(0)
    products, principal = _summarize_graph_change(
        reactants, graph, principal_origins
    )
    return products, changes, reactants, principal


def _run_radical_hbr_addition(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, ["hydrogen-bromide"], reagent_counts, step_number
    )
    alkene = reactants[0]
    double_bonds = _unsaturated_bonds(alkene, Chem.BondType.DOUBLE)
    if len(double_bonds) != 1:
        raise PlannerInputError("Radical HBr addition requires one terminal alkene.")
    carbon_a, carbon_b = double_bonds[0]
    terminal = next(
        (
            atom_index
            for atom_index in (carbon_a, carbon_b)
            if sum(
                neighbor.GetAtomicNum() == 6
                for neighbor in alkene.GetAtomWithIdx(atom_index).GetNeighbors()
            )
            == 1
        ),
        None,
    )
    if terminal is None:
        raise PlannerInputError("Radical HBr addition requires a terminal alkene.")
    internal = carbon_b if terminal == carbon_a else carbon_a
    bromine = next(
        atom.GetIdx()
        for atom in reactants[1].GetAtoms()
        if atom.GetAtomicNum() == 35
    )
    hydrogen = _hydrogen_neighbor(reactants[1], bromine)
    graph, offsets = _combine_reactants(reactants)
    terminal += offsets[0]
    internal += offsets[0]
    bromine += offsets[1]
    hydrogen += offsets[1]
    principal_origin = _origin(graph.GetAtomWithIdx(terminal))
    changes = []
    _append_bond_change(changes, "bond order changed", graph, terminal, internal)
    _append_bond_change(changes, "broken", graph, bromine, hydrogen)
    _append_bond_change(changes, "formed", graph, terminal, bromine)
    _append_bond_change(changes, "formed", graph, internal, hydrogen)
    graph.GetBondBetweenAtoms(terminal, internal).SetBondType(Chem.BondType.SINGLE)
    graph.RemoveBond(bromine, hydrogen)
    graph.AddBond(terminal, bromine, Chem.BondType.SINGLE)
    graph.AddBond(internal, hydrogen, Chem.BondType.SINGLE)
    products, principal = _summarize_graph_change(
        reactants, graph, [principal_origin]
    )
    return products, changes, reactants, principal


def _peroxide_atoms(molecule: Chem.Mol) -> tuple[int, int, int, int]:
    oxygen_atoms = [atom.GetIdx() for atom in molecule.GetAtoms() if atom.GetAtomicNum() == 8]
    if len(oxygen_atoms) != 2 or not molecule.GetBondBetweenAtoms(*oxygen_atoms):
        raise PlannerInputError("Peroxide oxidation requires an explicit hydrogen peroxide molecule.")
    first, second = oxygen_atoms
    if molecule.GetBondBetweenAtoms(first, second).GetBondType() != Chem.BondType.SINGLE:
        raise PlannerInputError("The hydrogen peroxide O-O bond is not single.")
    return (
        first,
        second,
        _hydrogen_neighbor(molecule, first),
        _hydrogen_neighbor(molecule, second),
    )


def _transfer_hydrogen(
    graph: Chem.RWMol,
    changes: list[dict[str, Any]],
    donor: int,
    acceptor: int,
    hydrogen: int,
) -> None:
    _append_bond_change(changes, "broken", graph, donor, hydrogen)
    _append_bond_change(changes, "formed", graph, acceptor, hydrogen)
    graph.RemoveBond(donor, hydrogen)
    graph.AddBond(acceptor, hydrogen, Chem.BondType.SINGLE)


def _run_alcohol_oxidation(
    rule: dict[str, Any],
    materials: list[dict[str, Any]],
    reagent_counts: dict[str, int],
    step_number: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, list(rule["reagents"]), reagent_counts, step_number
    )
    alcohol = reactants[0]
    alcohol_oxygen = next(
        atom.GetIdx()
        for atom in alcohol.GetAtoms()
        if atom.GetAtomicNum() == 8 and atom.GetTotalNumHs(includeNeighbors=True) == 1
    )
    carbon = next(
        neighbor.GetIdx()
        for neighbor in alcohol.GetAtomWithIdx(alcohol_oxygen).GetNeighbors()
        if neighbor.GetAtomicNum() == 6
    )
    alcohol_hydrogen = _hydrogen_neighbor(alcohol, alcohol_oxygen)
    carbon_hydrogens = [
        atom.GetIdx()
        for atom in alcohol.GetAtomWithIdx(carbon).GetNeighbors()
        if atom.GetAtomicNum() == 1
    ]
    executor = rule["executor"]
    if executor == "primary-alcohol-to-carboxylic-acid":
        if len(carbon_hydrogens) not in {2, 3} or len(reactants) != 3:
            raise PlannerInputError("Acid oxidation requires one primary alcohol and two peroxides.")
    elif executor == "secondary-alcohol-to-ketone":
        if len(carbon_hydrogens) != 1 or len(reactants) != 2:
            raise PlannerInputError("Ketone oxidation requires one secondary alcohol and one peroxide.")
    else:
        raise PlannerInputError(f"Unknown alcohol oxidation executor {executor!r}.")

    graph, offsets = _combine_reactants(reactants)
    oxygen_index = alcohol_oxygen + offsets[0]
    carbon_index = carbon + offsets[0]
    alcohol_hydrogen += offsets[0]
    carbon_hydrogens = [hydrogen + offsets[0] for hydrogen in carbon_hydrogens]
    graph.GetBondBetweenAtoms(carbon_index, oxygen_index).SetBondType(Chem.BondType.DOUBLE)
    changes = [
        {
            "change": "bond order changed",
            "from": _atom_ref(graph.GetAtomWithIdx(carbon_index)),
            "to": _atom_ref(graph.GetAtomWithIdx(oxygen_index)),
            "fromBondOrder": 1,
            "toBondOrder": 2,
        }
    ]

    peroxide_atoms = [
        _peroxide_atoms(molecule)
        for molecule in reactants[1:]
    ]
    if executor == "secondary-alcohol-to-ketone":
        oxygen_a, oxygen_b, _hydrogen_a, _hydrogen_b = peroxide_atoms[0]
        oxygen_a += offsets[1]
        oxygen_b += offsets[1]
        _append_bond_change(changes, "broken", graph, oxygen_a, oxygen_b)
        graph.RemoveBond(oxygen_a, oxygen_b)
        _transfer_hydrogen(
            graph, changes, oxygen_index, oxygen_a, alcohol_hydrogen
        )
        _transfer_hydrogen(
            graph, changes, carbon_index, oxygen_b, carbon_hydrogens[0]
        )
    else:
        first_a, first_b, _first_h_a, _first_h_b = peroxide_atoms[0]
        second_a, second_b, _second_h_a, _second_h_b = peroxide_atoms[1]
        first_a += offsets[1]
        first_b += offsets[1]
        second_a += offsets[2]
        second_b += offsets[2]
        _append_bond_change(changes, "broken", graph, first_a, first_b)
        _append_bond_change(changes, "broken", graph, second_a, second_b)
        graph.RemoveBond(first_a, first_b)
        graph.RemoveBond(second_a, second_b)
        graph.AddBond(carbon_index, first_a, Chem.BondType.SINGLE)
        changes.append(
            {
                "change": "formed",
                "from": _atom_ref(graph.GetAtomWithIdx(carbon_index)),
                "to": _atom_ref(graph.GetAtomWithIdx(first_a)),
            }
        )
        _transfer_hydrogen(
            graph, changes, oxygen_index, first_b, alcohol_hydrogen
        )
        for carbon_hydrogen, acceptor in zip(carbon_hydrogens, (second_a, second_b)):
            _transfer_hydrogen(
                graph, changes, carbon_index, acceptor, carbon_hydrogen
            )

    principal_origin = _origin(graph.GetAtomWithIdx(carbon_index))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_primary_alcohol_to_aldehyde(
    rule: dict[str, Any],
    materials: list[dict[str, Any]],
    reagent_counts: dict[str, int],
    step_number: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, list(rule["reagents"]), reagent_counts, step_number
    )
    alcohol = reactants[0]
    oxygen = next(
        atom.GetIdx()
        for atom in alcohol.GetAtoms()
        if atom.GetAtomicNum() == 8 and atom.GetTotalNumHs(includeNeighbors=True) == 1
    )
    carbon = next(
        neighbor.GetIdx()
        for neighbor in alcohol.GetAtomWithIdx(oxygen).GetNeighbors()
        if neighbor.GetAtomicNum() == 6
    )
    alcohol_hydrogen = _hydrogen_neighbor(alcohol, oxygen)
    carbon_hydrogen = _hydrogen_neighbor(alcohol, carbon)
    oxidant = reactants[1]
    hypochlorite_oxygen = next(
        atom.GetIdx()
        for atom in oxidant.GetAtoms()
        if atom.GetAtomicNum() == 8 and atom.GetFormalCharge() == -1
    )
    chlorine = next(
        neighbor.GetIdx()
        for neighbor in oxidant.GetAtomWithIdx(hypochlorite_oxygen).GetNeighbors()
        if neighbor.GetAtomicNum() == 17
    )
    graph, offsets = _combine_reactants(reactants)
    oxygen += offsets[0]
    carbon += offsets[0]
    alcohol_hydrogen += offsets[0]
    carbon_hydrogen += offsets[0]
    hypochlorite_oxygen += offsets[1]
    chlorine += offsets[1]
    graph.GetBondBetweenAtoms(carbon, oxygen).SetBondType(Chem.BondType.DOUBLE)
    graph.RemoveBond(hypochlorite_oxygen, chlorine)
    graph.GetAtomWithIdx(hypochlorite_oxygen).SetFormalCharge(0)
    graph.GetAtomWithIdx(chlorine).SetFormalCharge(-1)
    changes = [
        {
            "change": "bond order changed",
            "from": _atom_ref(graph.GetAtomWithIdx(carbon)),
            "to": _atom_ref(graph.GetAtomWithIdx(oxygen)),
            "fromBondOrder": 1,
            "toBondOrder": 2,
        },
        {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(hypochlorite_oxygen)), "to": _atom_ref(graph.GetAtomWithIdx(chlorine))},
    ]
    _transfer_hydrogen(
        graph, changes, oxygen, hypochlorite_oxygen, alcohol_hydrogen
    )
    _transfer_hydrogen(
        graph, changes, carbon, hypochlorite_oxygen, carbon_hydrogen
    )
    principal_origin = _origin(graph.GetAtomWithIdx(carbon))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_aldehyde_oxidation(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(materials, ["hydrogen-peroxide"], reagent_counts, step_number)
    aldehyde = reactants[0]
    site = _aldehyde_site(aldehyde)
    if site is None:
        raise PlannerInputError("Aldehyde oxidation requires one aldehyde group.")
    carbon, carbonyl_oxygen = site
    aldehyde_hydrogen = _hydrogen_neighbor(aldehyde, carbon)
    graph, offsets = _combine_reactants(reactants)
    carbon += offsets[0]
    carbonyl_oxygen += offsets[0]
    aldehyde_hydrogen += offsets[0]
    peroxide_oxygen, water_oxygen, _peroxide_h, _water_h = _peroxide_atoms(reactants[1])
    peroxide_oxygen += offsets[1]
    water_oxygen += offsets[1]
    graph.RemoveBond(peroxide_oxygen, water_oxygen)
    graph.AddBond(carbon, peroxide_oxygen, Chem.BondType.SINGLE)
    changes = []
    _append_bond_change(changes, "broken", graph, peroxide_oxygen, water_oxygen)
    _append_bond_change(changes, "formed", graph, carbon, peroxide_oxygen)
    peroxide_hydrogen = _hydrogen_neighbor(graph, peroxide_oxygen)
    water_hydrogen = _hydrogen_neighbor(graph, water_oxygen)
    _transfer_hydrogen(
        graph, changes, carbon, water_oxygen, aldehyde_hydrogen
    )
    principal_origin = _origin(graph.GetAtomWithIdx(carbon))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_aldehyde_hydrogenation(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(materials, ["hydrogen"], reagent_counts, step_number)
    site = _aldehyde_site(reactants[0])
    hydrogen_atoms = [atom.GetIdx() for atom in reactants[1].GetAtoms() if atom.GetAtomicNum() == 1]
    if site is None or len(hydrogen_atoms) != 2:
        raise PlannerInputError("Aldehyde hydrogenation requires one aldehyde and one H2 molecule.")
    carbon, oxygen = site
    graph, offsets = _combine_reactants(reactants)
    carbon += offsets[0]
    oxygen += offsets[0]
    hydrogen_a, hydrogen_b = (index + offsets[1] for index in hydrogen_atoms)
    graph.GetBondBetweenAtoms(carbon, oxygen).SetBondType(Chem.BondType.SINGLE)
    graph.RemoveBond(hydrogen_a, hydrogen_b)
    graph.AddBond(carbon, hydrogen_a, Chem.BondType.SINGLE)
    graph.AddBond(oxygen, hydrogen_b, Chem.BondType.SINGLE)
    changes = [
        {
            "change": "bond order changed",
            "from": _atom_ref(graph.GetAtomWithIdx(carbon)),
            "to": _atom_ref(graph.GetAtomWithIdx(oxygen)),
            "fromBondOrder": 2,
            "toBondOrder": 1,
        },
        {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(hydrogen_a)), "to": _atom_ref(graph.GetAtomWithIdx(hydrogen_b))},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(carbon)), "to": _atom_ref(graph.GetAtomWithIdx(hydrogen_a))},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(oxygen)), "to": _atom_ref(graph.GetAtomWithIdx(hydrogen_b))},
    ]
    principal_origin = _origin(graph.GetAtomWithIdx(carbon))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_aromatic_substitution(
    rule: dict[str, Any],
    materials: list[dict[str, Any]],
    reagent_counts: dict[str, int],
    step_number: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, list(rule["reagents"]), reagent_counts, step_number
    )
    arene = reactants[0]
    ring_carbon = next(
        (
            atom.GetIdx()
            for atom in arene.GetAtoms()
            if atom.GetIsAromatic()
            and atom.GetAtomicNum() == 6
            and any(neighbor.GetAtomicNum() == 1 for neighbor in atom.GetNeighbors())
        ),
        None,
    )
    if ring_carbon is None:
        raise PlannerInputError("Aromatic substitution requires a benzene C-H site.")
    ring_hydrogen = _hydrogen_neighbor(arene, ring_carbon)
    graph, offsets = _combine_reactants(reactants)
    ring_carbon += offsets[0]
    ring_hydrogen += offsets[0]
    changes = []
    executor = rule["executor"]

    if executor == "benzene-nitration":
        nitric = reactants[1]
        nitrogen = next(atom.GetIdx() for atom in nitric.GetAtoms() if atom.GetAtomicNum() == 7)
        leaving_oxygen = next(
            atom.GetIdx()
            for atom in nitric.GetAtoms()
            if atom.GetAtomicNum() == 8
            and atom.GetTotalNumHs(includeNeighbors=True) == 1
            and any(neighbor.GetAtomicNum() == 7 for neighbor in atom.GetNeighbors())
        )
        nitrogen += offsets[1]
        leaving_oxygen += offsets[1]
        graph.RemoveBond(nitrogen, leaving_oxygen)
        graph.AddBond(nitrogen, ring_carbon, Chem.BondType.SINGLE)
        graph.AddBond(leaving_oxygen, ring_hydrogen, Chem.BondType.SINGLE)
        changes.extend(
            [
                {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(nitrogen)), "to": _atom_ref(graph.GetAtomWithIdx(leaving_oxygen))},
                {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(nitrogen)), "to": _atom_ref(graph.GetAtomWithIdx(ring_carbon))},
                {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(ring_carbon)), "to": _atom_ref(graph.GetAtomWithIdx(ring_hydrogen))},
                {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(leaving_oxygen)), "to": _atom_ref(graph.GetAtomWithIdx(ring_hydrogen))},
            ]
        )
        graph.RemoveBond(ring_carbon, ring_hydrogen)
    elif executor in {"benzene-acylation", "benzene-ethylation"}:
        electrophile = reactants[1]
        chlorine = next(atom.GetIdx() for atom in electrophile.GetAtoms() if atom.GetAtomicNum() == 17)
        electrophilic_carbon = next(
            neighbor.GetIdx()
            for neighbor in electrophile.GetAtomWithIdx(chlorine).GetNeighbors()
            if neighbor.GetAtomicNum() == 6
        )
        chlorine += offsets[1]
        electrophilic_carbon += offsets[1]
        graph.RemoveBond(electrophilic_carbon, chlorine)
        graph.RemoveBond(ring_carbon, ring_hydrogen)
        graph.AddBond(electrophilic_carbon, ring_carbon, Chem.BondType.SINGLE)
        graph.AddBond(chlorine, ring_hydrogen, Chem.BondType.SINGLE)
        changes.extend(
            [
                {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(electrophilic_carbon)), "to": _atom_ref(graph.GetAtomWithIdx(chlorine))},
                {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(electrophilic_carbon)), "to": _atom_ref(graph.GetAtomWithIdx(ring_carbon))},
                {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(ring_carbon)), "to": _atom_ref(graph.GetAtomWithIdx(ring_hydrogen))},
                {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(chlorine)), "to": _atom_ref(graph.GetAtomWithIdx(ring_hydrogen))},
            ]
        )
    else:
        raise PlannerInputError(f"Unknown aromatic substitution executor {executor!r}.")

    principal_origin = _origin(graph.GetAtomWithIdx(ring_carbon))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_anhydride_acetylation(
    rule: dict[str, Any],
    materials: list[dict[str, Any]],
    reagent_counts: dict[str, int],
    step_number: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, list(rule["reagents"]), reagent_counts, step_number
    )
    substrate = reactants[0]
    if rule["executor"] == "phenolic-o-acetylation":
        donor = next(
            atom.GetIdx()
            for atom in substrate.GetAtoms()
            if atom.GetAtomicNum() == 8
            and atom.GetTotalNumHs(includeNeighbors=True) == 1
            and any(neighbor.GetIsAromatic() for neighbor in atom.GetNeighbors())
        )
    else:
        donor = next(
            atom.GetIdx()
            for atom in substrate.GetAtoms()
            if atom.GetAtomicNum() == 7
            and atom.GetTotalNumHs(includeNeighbors=True) == 2
            and any(neighbor.GetIsAromatic() for neighbor in atom.GetNeighbors())
        )
    transfer_hydrogen = _hydrogen_neighbor(substrate, donor)
    anhydride = reactants[1]
    acyl_carbon, _carbonyl_oxygen = _carbonyl_centres(anhydride)[0]
    bridge_oxygen = next(
        neighbor.GetIdx()
        for neighbor in anhydride.GetAtomWithIdx(acyl_carbon).GetNeighbors()
        if neighbor.GetAtomicNum() == 8
        and len(
            [adjacent for adjacent in neighbor.GetNeighbors() if adjacent.GetAtomicNum() == 6]
        )
        == 2
    )
    graph, offsets = _combine_reactants(reactants)
    donor += offsets[0]
    transfer_hydrogen += offsets[0]
    acyl_carbon += offsets[1]
    bridge_oxygen += offsets[1]
    graph.RemoveBond(acyl_carbon, bridge_oxygen)
    graph.RemoveBond(donor, transfer_hydrogen)
    graph.AddBond(acyl_carbon, donor, Chem.BondType.SINGLE)
    graph.AddBond(bridge_oxygen, transfer_hydrogen, Chem.BondType.SINGLE)
    changes = [
        {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(acyl_carbon)), "to": _atom_ref(graph.GetAtomWithIdx(bridge_oxygen))},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(acyl_carbon)), "to": _atom_ref(graph.GetAtomWithIdx(donor))},
        {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(donor)), "to": _atom_ref(graph.GetAtomWithIdx(transfer_hydrogen))},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(bridge_oxygen)), "to": _atom_ref(graph.GetAtomWithIdx(transfer_hydrogen))},
    ]
    principal_origin = _origin(graph.GetAtomWithIdx(donor))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_phenoxide_formation(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(materials, ["sodium-hydroxide"], reagent_counts, step_number)
    phenol = reactants[0]
    phenolic_oxygen = next(
        atom.GetIdx()
        for atom in phenol.GetAtoms()
        if atom.GetAtomicNum() == 8
        and atom.GetTotalNumHs(includeNeighbors=True) == 1
        and any(neighbor.GetIsAromatic() for neighbor in atom.GetNeighbors())
    )
    phenolic_hydrogen = _hydrogen_neighbor(phenol, phenolic_oxygen)
    hydroxide_oxygen = next(
        atom.GetIdx()
        for atom in reactants[1].GetAtoms()
        if atom.GetAtomicNum() == 8 and atom.GetFormalCharge() == -1
    )
    graph, offsets = _combine_reactants(reactants)
    phenolic_oxygen += offsets[0]
    phenolic_hydrogen += offsets[0]
    hydroxide_oxygen += offsets[1]
    graph.RemoveBond(phenolic_oxygen, phenolic_hydrogen)
    graph.AddBond(hydroxide_oxygen, phenolic_hydrogen, Chem.BondType.SINGLE)
    graph.GetAtomWithIdx(phenolic_oxygen).SetFormalCharge(-1)
    graph.GetAtomWithIdx(hydroxide_oxygen).SetFormalCharge(0)
    changes = [
        {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(phenolic_oxygen)), "to": _atom_ref(graph.GetAtomWithIdx(phenolic_hydrogen))},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(hydroxide_oxygen)), "to": _atom_ref(graph.GetAtomWithIdx(phenolic_hydrogen))},
    ]
    principal_origin = _origin(graph.GetAtomWithIdx(phenolic_oxygen))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_kolbe_schmitt(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(materials, [], reagent_counts, step_number)
    phenoxide, carbon_dioxide = reactants
    phenolic_oxygen = next(
        atom.GetIdx()
        for atom in phenoxide.GetAtoms()
        if atom.GetAtomicNum() == 8
        and atom.GetFormalCharge() == -1
        and any(neighbor.GetIsAromatic() for neighbor in atom.GetNeighbors())
    )
    ipso_carbon = next(
        neighbor.GetIdx()
        for neighbor in phenoxide.GetAtomWithIdx(phenolic_oxygen).GetNeighbors()
        if neighbor.GetIsAromatic()
    )
    ortho_carbon = next(
        neighbor.GetIdx()
        for neighbor in phenoxide.GetAtomWithIdx(ipso_carbon).GetNeighbors()
        if neighbor.GetIsAromatic()
        and any(hydrogen.GetAtomicNum() == 1 for hydrogen in neighbor.GetNeighbors())
    )
    ring_hydrogen = _hydrogen_neighbor(phenoxide, ortho_carbon)
    carboxyl_carbon, carbonyl_oxygen = _carbonyl_centres(carbon_dioxide)[0]
    carboxylate_oxygen = next(
        atom.GetIdx()
        for atom in carbon_dioxide.GetAtoms()
        if atom.GetAtomicNum() == 8 and atom.GetIdx() != carbonyl_oxygen
    )
    graph, offsets = _combine_reactants(reactants)
    phenolic_oxygen += offsets[0]
    ortho_carbon += offsets[0]
    ring_hydrogen += offsets[0]
    carboxyl_carbon += offsets[1]
    carbonyl_oxygen += offsets[1]
    carboxylate_oxygen += offsets[1]
    graph.RemoveBond(ortho_carbon, ring_hydrogen)
    graph.AddBond(phenolic_oxygen, ring_hydrogen, Chem.BondType.SINGLE)
    graph.AddBond(ortho_carbon, carboxyl_carbon, Chem.BondType.SINGLE)
    graph.GetBondBetweenAtoms(carboxyl_carbon, carboxylate_oxygen).SetBondType(
        Chem.BondType.SINGLE
    )
    graph.GetAtomWithIdx(phenolic_oxygen).SetFormalCharge(0)
    graph.GetAtomWithIdx(carboxylate_oxygen).SetFormalCharge(-1)
    changes = [
        {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(ortho_carbon)), "to": _atom_ref(graph.GetAtomWithIdx(ring_hydrogen))},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(phenolic_oxygen)), "to": _atom_ref(graph.GetAtomWithIdx(ring_hydrogen))},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(ortho_carbon)), "to": _atom_ref(graph.GetAtomWithIdx(carboxyl_carbon))},
        {
            "change": "bond order changed",
            "from": _atom_ref(graph.GetAtomWithIdx(carboxyl_carbon)),
            "to": _atom_ref(graph.GetAtomWithIdx(carboxylate_oxygen)),
            "fromBondOrder": 2,
            "toBondOrder": 1,
        },
    ]
    principal_origin = _origin(graph.GetAtomWithIdx(carboxyl_carbon))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_strecker_imine_formation(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(materials, [], reagent_counts, step_number)
    aldehyde, ammonia = reactants
    site = _aldehyde_site(aldehyde)
    if site is None:
        raise PlannerInputError("Strecker imine formation requires an aldehyde.")
    carbon, oxygen = site
    nitrogen = next(atom.GetIdx() for atom in ammonia.GetAtoms() if atom.GetAtomicNum() == 7)
    nitrogen_hydrogens = [
        atom.GetIdx()
        for atom in ammonia.GetAtomWithIdx(nitrogen).GetNeighbors()
        if atom.GetAtomicNum() == 1
    ]
    if len(nitrogen_hydrogens) != 3:
        raise PlannerInputError("Imine formation requires ammonia with three explicit hydrogens.")
    graph, offsets = _combine_reactants(reactants)
    carbon += offsets[0]
    oxygen += offsets[0]
    nitrogen += offsets[1]
    nitrogen_hydrogens = [hydrogen + offsets[1] for hydrogen in nitrogen_hydrogens]
    graph.RemoveBond(carbon, oxygen)
    graph.AddBond(carbon, nitrogen, Chem.BondType.DOUBLE)
    changes = [
        {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(carbon)), "to": _atom_ref(graph.GetAtomWithIdx(oxygen))},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(carbon)), "to": _atom_ref(graph.GetAtomWithIdx(nitrogen))},
    ]
    for hydrogen in nitrogen_hydrogens[:2]:
        _transfer_hydrogen(graph, changes, nitrogen, oxygen, hydrogen)
    principal_origin = _origin(graph.GetAtomWithIdx(carbon))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_strecker_cyanide_addition(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(materials, [], reagent_counts, step_number)
    imine, hydrogen_cyanide = reactants
    imine_bond = next(
        bond
        for bond in imine.GetBonds()
        if bond.GetBondType() == Chem.BondType.DOUBLE
        and {bond.GetBeginAtom().GetAtomicNum(), bond.GetEndAtom().GetAtomicNum()} == {6, 7}
    )
    carbon = next(
        atom.GetIdx()
        for atom in (imine_bond.GetBeginAtom(), imine_bond.GetEndAtom())
        if atom.GetAtomicNum() == 6
    )
    nitrogen = imine_bond.GetOtherAtomIdx(carbon)
    cyanide_carbon = next(
        atom.GetIdx() for atom in hydrogen_cyanide.GetAtoms() if atom.GetAtomicNum() == 6
    )
    cyanide_nitrogen = next(
        atom.GetIdx() for atom in hydrogen_cyanide.GetAtoms() if atom.GetAtomicNum() == 7
    )
    cyanide_hydrogen = _hydrogen_neighbor(hydrogen_cyanide, cyanide_carbon)
    graph, offsets = _combine_reactants(reactants)
    carbon += offsets[0]
    nitrogen += offsets[0]
    cyanide_carbon += offsets[1]
    cyanide_nitrogen += offsets[1]
    cyanide_hydrogen += offsets[1]
    graph.GetBondBetweenAtoms(carbon, nitrogen).SetBondType(Chem.BondType.SINGLE)
    graph.RemoveBond(cyanide_carbon, cyanide_hydrogen)
    graph.AddBond(carbon, cyanide_carbon, Chem.BondType.SINGLE)
    graph.AddBond(nitrogen, cyanide_hydrogen, Chem.BondType.SINGLE)
    changes = [
        {
            "change": "bond order changed",
            "from": _atom_ref(graph.GetAtomWithIdx(carbon)),
            "to": _atom_ref(graph.GetAtomWithIdx(nitrogen)),
            "fromBondOrder": 2,
            "toBondOrder": 1,
        },
        {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(cyanide_carbon)), "to": _atom_ref(graph.GetAtomWithIdx(cyanide_hydrogen))},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(carbon)), "to": _atom_ref(graph.GetAtomWithIdx(cyanide_carbon))},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(nitrogen)), "to": _atom_ref(graph.GetAtomWithIdx(cyanide_hydrogen))},
    ]
    principal_origin = _origin(graph.GetAtomWithIdx(carbon))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_aminonitrile_hydrolysis(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(
        materials, ["water", "sodium-hydroxide"], reagent_counts, step_number
    )
    aminonitrile = reactants[0]
    nitrile_bond = next(
        bond
        for bond in aminonitrile.GetBonds()
        if bond.GetBondType() == Chem.BondType.TRIPLE
        and {bond.GetBeginAtom().GetAtomicNum(), bond.GetEndAtom().GetAtomicNum()} == {6, 7}
    )
    carbon = next(
        atom.GetIdx()
        for atom in (nitrile_bond.GetBeginAtom(), nitrile_bond.GetEndAtom())
        if atom.GetAtomicNum() == 6
    )
    nitrogen = nitrile_bond.GetOtherAtomIdx(carbon)
    water = reactants[1]
    water_oxygen = next(
        atom.GetIdx()
        for atom in water.GetAtoms()
        if atom.GetAtomicNum() == 8 and atom.GetFormalCharge() == 0
    )
    water_hydrogens = [
        atom.GetIdx()
        for atom in water.GetAtomWithIdx(water_oxygen).GetNeighbors()
        if atom.GetAtomicNum() == 1
    ]
    hydroxide = reactants[2]
    hydroxide_oxygen = next(
        atom.GetIdx()
        for atom in hydroxide.GetAtoms()
        if atom.GetAtomicNum() == 8 and atom.GetFormalCharge() == -1
    )
    hydroxide_hydrogen = _hydrogen_neighbor(hydroxide, hydroxide_oxygen)
    if len(water_hydrogens) != 2:
        raise PlannerInputError("Nitrile hydrolysis requires one explicit water molecule.")
    graph, offsets = _combine_reactants(reactants)
    carbon += offsets[0]
    nitrogen += offsets[0]
    water_oxygen += offsets[1]
    water_hydrogens = [hydrogen + offsets[1] for hydrogen in water_hydrogens]
    hydroxide_oxygen += offsets[2]
    hydroxide_hydrogen += offsets[2]
    graph.RemoveBond(carbon, nitrogen)
    graph.AddBond(carbon, hydroxide_oxygen, Chem.BondType.DOUBLE)
    graph.AddBond(carbon, water_oxygen, Chem.BondType.SINGLE)
    graph.GetAtomWithIdx(hydroxide_oxygen).SetFormalCharge(0)
    graph.GetAtomWithIdx(water_oxygen).SetFormalCharge(-1)
    changes = [
        {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(carbon)), "to": _atom_ref(graph.GetAtomWithIdx(nitrogen)), "fromBondOrder": 3},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(carbon)), "to": _atom_ref(graph.GetAtomWithIdx(hydroxide_oxygen)), "toBondOrder": 2},
        {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(carbon)), "to": _atom_ref(graph.GetAtomWithIdx(water_oxygen)), "toBondOrder": 1},
    ]
    for hydrogen in water_hydrogens:
        _transfer_hydrogen(graph, changes, water_oxygen, nitrogen, hydrogen)
    _transfer_hydrogen(
        graph, changes, hydroxide_oxygen, nitrogen, hydroxide_hydrogen
    )
    principal_origin = _origin(graph.GetAtomWithIdx(carbon))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


def _run_paal_knorr_pyrrole(
    materials: list[dict[str, Any]], reagent_counts: dict[str, int], step_number: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    reactants = _reactant_set(materials, [], reagent_counts, step_number)
    dialdehyde, ammonia = reactants
    carbonyl_sites = _carbonyl_centres(dialdehyde)
    terminal_carbons = [carbon for carbon, _oxygen in carbonyl_sites]
    if len(terminal_carbons) != 2:
        raise PlannerInputError("Paal-Knorr pyrrole synthesis requires two terminal aldehydes.")
    chain = [terminal_carbons[0]]
    previous = None
    while chain[-1] != terminal_carbons[1]:
        next_carbon = next(
            (
                neighbor.GetIdx()
                for neighbor in dialdehyde.GetAtomWithIdx(chain[-1]).GetNeighbors()
                if neighbor.GetAtomicNum() == 6 and neighbor.GetIdx() != previous
            ),
            None,
        )
        if next_carbon is None or next_carbon in chain:
            raise PlannerInputError("The dialdehyde carbon chain is not a linear four-carbon chain.")
        previous, current = chain[-1], next_carbon
        chain.append(current)
    if len(chain) != 4:
        raise PlannerInputError("Paal-Knorr pyrrole synthesis requires a four-carbon chain.")

    oxygen_by_carbon = dict(carbonyl_sites)
    internal_hydrogens = [
        [
            atom.GetIdx()
            for atom in dialdehyde.GetAtomWithIdx(carbon).GetNeighbors()
            if atom.GetAtomicNum() == 1
        ]
        for carbon in chain[1:3]
    ]
    nitrogen = next(atom.GetIdx() for atom in ammonia.GetAtoms() if atom.GetAtomicNum() == 7)
    nitrogen_hydrogens = [
        atom.GetIdx()
        for atom in ammonia.GetAtomWithIdx(nitrogen).GetNeighbors()
        if atom.GetAtomicNum() == 1
    ]
    if len(nitrogen_hydrogens) != 3 or any(len(hydrogens) != 2 for hydrogens in internal_hydrogens):
        raise PlannerInputError("Paal-Knorr pyrrole synthesis requires the specified dialdehyde and ammonia.")

    graph, offsets = _combine_reactants(reactants)
    substrate_offset, ammonia_offset = offsets
    chain = [carbon + substrate_offset for carbon in chain]
    nitrogen += ammonia_offset
    nitrogen_hydrogens = [
        hydrogen + ammonia_offset for hydrogen in nitrogen_hydrogens
    ]
    oxygen_by_carbon = {
        carbon + substrate_offset: oxygen + substrate_offset
        for carbon, oxygen in oxygen_by_carbon.items()
    }
    internal_hydrogens = [
        [hydrogen + substrate_offset for hydrogen in hydrogens[:1]]
        for hydrogens in internal_hydrogens
    ]
    changes = []
    for carbon in (chain[0], chain[-1]):
        oxygen = oxygen_by_carbon[carbon]
        graph.RemoveBond(carbon, oxygen)
        graph.AddBond(carbon, nitrogen, Chem.BondType.SINGLE)
        changes.extend(
            [
                {"change": "broken", "from": _atom_ref(graph.GetAtomWithIdx(carbon)), "to": _atom_ref(graph.GetAtomWithIdx(oxygen)), "fromBondOrder": 2},
                {"change": "formed", "from": _atom_ref(graph.GetAtomWithIdx(carbon)), "to": _atom_ref(graph.GetAtomWithIdx(nitrogen)), "toBondOrder": 1},
            ]
        )
    for left, right in ((chain[0], chain[1]), (chain[2], chain[3])):
        graph.GetBondBetweenAtoms(left, right).SetBondType(Chem.BondType.DOUBLE)
        changes.append(
            {
                "change": "bond order changed",
                "from": _atom_ref(graph.GetAtomWithIdx(left)),
                "to": _atom_ref(graph.GetAtomWithIdx(right)),
                "fromBondOrder": 1,
                "toBondOrder": 2,
            }
        )
    oxygen_a = oxygen_by_carbon[chain[0]]
    oxygen_b = oxygen_by_carbon[chain[-1]]
    _transfer_hydrogen(
        graph, changes, nitrogen, oxygen_a, nitrogen_hydrogens[0]
    )
    _transfer_hydrogen(
        graph, changes, nitrogen, oxygen_b, nitrogen_hydrogens[1]
    )
    _transfer_hydrogen(
        graph, changes, chain[1], oxygen_a, internal_hydrogens[0][0]
    )
    _transfer_hydrogen(
        graph, changes, chain[2], oxygen_b, internal_hydrogens[1][0]
    )
    principal_origin = _origin(graph.GetAtomWithIdx(chain[0]))
    products, principal = _summarize_graph_change(reactants, graph, [principal_origin])
    return products, changes, reactants, principal


EXECUTORS = {
    "acyl-ammonia": _run_acyl_substitution,
    "acyl-amine": _run_acyl_substitution,
    "acyl-alcohol": _run_acyl_substitution,
    "acyl-water": _run_acyl_substitution,
    "acyl-carboxylate": _run_acyl_substitution,
    "acid-thionyl-chloride": _run_acid_chloride_formation,
    "ester-hydroxide": _run_ester_saponification,
    "fischer-esterification": _run_fischer_esterification,
    "carboxylate-acidification": _run_carboxylate_acidification,
    "hydrogenation-alkene": _run_hydrogenation,
    "hydrogenation-alkyne": _run_hydrogenation,
    "ozonolysis": _run_ozonolysis,
    "radical-hbr-addition": _run_radical_hbr_addition,
    "primary-alcohol-to-aldehyde": _run_primary_alcohol_to_aldehyde,
    "primary-alcohol-to-carboxylic-acid": _run_alcohol_oxidation,
    "secondary-alcohol-to-ketone": _run_alcohol_oxidation,
    "aldehyde-to-carboxylic-acid": _run_aldehyde_oxidation,
    "aldehyde-hydrogenation": _run_aldehyde_hydrogenation,
    "benzene-nitration": _run_aromatic_substitution,
    "benzene-acylation": _run_aromatic_substitution,
    "benzene-ethylation": _run_aromatic_substitution,
    "phenolic-o-acetylation": _run_anhydride_acetylation,
    "aniline-n-acetylation": _run_anhydride_acetylation,
    "phenoxide-formation": _run_phenoxide_formation,
    "kolbe-schmitt-carboxylation": _run_kolbe_schmitt,
    "strecker-imine-formation": _run_strecker_imine_formation,
    "strecker-cyanide-addition": _run_strecker_cyanide_addition,
    "aminonitrile-hydrolysis": _run_aminonitrile_hydrolysis,
    "paal-knorr-pyrrole": _run_paal_knorr_pyrrole,
}


def _is_goal(inventory: dict[InventoryKey, int], targets: list[dict[str, Any]]) -> bool:
    available = Counter()
    for lot, quantity in inventory.items():
        available[lot[0]] += quantity
    required = Counter()
    for target in targets:
        required[target["canonicalSmiles"]] += target["quantity"]
    return all(available[smiles] >= quantity for smiles, quantity in required.items())


def _inventory_signature(
    inventory: dict[InventoryKey, int],
    reagent_inventory: dict[str, int | None],
) -> tuple[Any, ...]:
    totals = Counter()
    for key, quantity in inventory.items():
        totals[key[0]] += quantity
    return (
        tuple(sorted(totals.items())),
        tuple(sorted(reagent_inventory.items())),
    )


def _add_products_to_inventory(
    inventory: dict[InventoryKey, int],
    products: list[dict[str, Any]],
    step_number: int,
) -> None:
    for index, product in enumerate(products, start=1):
        source_name = product.get("name") or product["formula"]
        key = (
            product["canonicalSmiles"],
            product.get("speciesId") or f"reaction-{step_number}-product-{index}",
            source_name,
            json.dumps(
                _canonical_atom_origins(
                    product["_sourceMol"], product["canonicalSmiles"]
                ),
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
        inventory[key] = inventory.get(key, 0) + 1


def _rule_reagents_available(
    rule: dict[str, Any], reagent_inventory: dict[str, int | None]
) -> bool:
    required_ids = set(rule["reagents"]) | set(rule.get("conditionsIds", []))
    if not required_ids.issubset(reagent_inventory):
        return False
    return all(
        reagent_inventory[reagent_id] is None
        or reagent_inventory[reagent_id] >= quantity
        for reagent_id, quantity in rule["reagents"].items()
    )


def _remaining_reagents(
    rule: dict[str, Any], reagent_inventory: dict[str, int | None]
) -> dict[str, int | None]:
    remaining = reagent_inventory.copy()
    for reagent_id, quantity in rule["reagents"].items():
        available = remaining[reagent_id]
        if available is not None:
            remaining[reagent_id] = available - quantity
    return remaining


def _material_choices(
    inventory: dict[InventoryKey, int],
    substrate_kind: str,
) -> list[str]:
    matcher = SUBSTRATE_MATCHERS[substrate_kind]
    smiles_choices = {
        key[0] for key, quantity in inventory.items() if quantity > 0
    }
    return sorted(
        smiles
        for smiles in smiles_choices
        if matcher(_read_molecule(smiles, "Available reaction substrate"))
    )


def _consume_materials(
    inventory: dict[InventoryKey, int],
    smiles: str,
    quantity: int,
) -> tuple[dict[InventoryKey, int], list[dict[str, Any]]] | None:
    next_inventory = inventory.copy()
    materials = []
    for key in sorted(inventory):
        if key[0] != smiles or next_inventory[key] <= 0:
            continue
        take = min(quantity, next_inventory[key])
        materials.extend(
            {
                "canonicalSmiles": key[0],
                "sourceId": key[1] if unit == 1 else f"{key[1]}-unit-{unit}",
                "sourceName": key[2],
                "atomOrigins": json.loads(key[3]),
            }
            for unit in range(1, take + 1)
        )
        next_inventory[key] -= take
        quantity -= take
        if quantity == 0:
            return next_inventory, materials
    return None


def _candidate_substrate_sets(
    rule: dict[str, Any],
    inventory: dict[InventoryKey, int],
) -> list[tuple[str, ...]]:
    substrate_kinds = rule["substrates"]
    quantities = rule.get("substrateQuantities", (1,) * len(substrate_kinds))
    choice_lists = [
        _material_choices(inventory, substrate_kind)
        for substrate_kind in substrate_kinds
    ]
    if any(not choices for choices in choice_lists):
        return []

    candidates = []
    seen = set()
    for selected in itertools.product(*choice_lists):
        if selected in seen:
            continue
        seen.add(selected)
        remaining = inventory
        available = True
        for smiles, quantity in zip(selected, quantities):
            consumed = _consume_materials(remaining, smiles, quantity)
            if consumed is None:
                available = False
                break
            remaining, _materials = consumed
        if available:
            candidates.append(selected)
    return candidates


def _materials_for_candidate(
    rule: dict[str, Any],
    selected: tuple[str, ...],
    inventory: dict[InventoryKey, int],
) -> tuple[dict[InventoryKey, int], list[dict[str, Any]]]:
    remaining = inventory
    materials = []
    quantities = rule.get("substrateQuantities", (1,) * len(selected))
    for smiles, quantity in zip(selected, quantities):
        consumed = _consume_materials(remaining, smiles, quantity)
        if consumed is None:
            raise PlannerInputError(
                "A selected reaction substrate was no longer present in the inventory.",
                code="planner_state_error",
                kind="internal",
            )
        remaining, selected_materials = consumed
        materials.extend(selected_materials)
    return remaining, materials


def _execute_rule(
    rule: dict[str, Any],
    materials: list[dict[str, Any]],
    step_number: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Chem.Mol], list[str]]:
    executor = EXECUTORS[rule["executor"]]
    if executor in {
        _run_acyl_substitution,
        _run_hydrogenation,
        _run_alcohol_oxidation,
        _run_primary_alcohol_to_aldehyde,
        _run_aromatic_substitution,
        _run_anhydride_acetylation,
    }:
        return executor(rule, materials, rule["reagents"], step_number)
    return executor(materials, rule["reagents"], step_number)


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
    input_materials: list[dict[str, Any]],
    step_number: int,
    principal_products: list[str],
) -> dict[str, Any]:
    public_products = []
    for index, product in enumerate(products, start=1):
        product["speciesId"] = f"reaction-{step_number}-product-{index}"
        product["role"] = (
            "desired product"
            if product["canonicalSmiles"] in principal_products
            else "coproduct"
        )
        public_products.append(
            {key: value for key, value in product.items() if not key.startswith("_")}
        )
    balance = _product_balance(reactants, public_products)
    if not balance["atomBalanceChecked"] or not balance["chargeBalanceChecked"]:
        raise PlannerInputError("A reaction failed its independent atom/charge-balance check.")
    input_species = [
        {
            "speciesId": material["sourceId"],
            "sourceType": "material",
            "name": material["sourceName"],
            "canonicalSmiles": material["canonicalSmiles"],
            "quantity": 1,
        }
        for material in input_materials
    ]
    reagent_inputs = []
    for reagent_id, quantity in rule["reagents"].items():
        reagent = REAGENT_CATALOGUE[reagent_id]
        smiles = reagent.get("smiles")
        if not smiles:
            continue
        canonical = _canonical_smiles(_read_molecule(smiles, "Reaction reagent"))
        for unit in range(1, quantity + 1):
            reagent_inputs.append(
                {
                    "speciesId": f"{reagent_id}-step-{step_number}-equivalent-{unit}",
                    "sourceType": "reagent",
                    "name": reagent["name"],
                    "formula": reagent["formula"],
                    "canonicalSmiles": canonical,
                    "quantity": 1,
                    "role": reagent["role"],
                }
            )
    return {
        "id": f"reaction-{step_number}",
        "step": step_number,
        "reactionId": rule["id"],
        "name": rule["name"],
        "family": rule["family"],
        "conditions": rule["conditions"],
        "shortDescription": rule["shortDescription"],
        "safetyNotes": rule["safetyNotes"],
        "stoichiometry": rule["stoichiometry"],
        "explanation": rule["mechanism"],
        "reagents": [
            {
                "id": reagent_id,
                "name": REAGENT_CATALOGUE[reagent_id]["name"],
                "formula": REAGENT_CATALOGUE[reagent_id]["formula"],
                "quantity": quantity,
                "role": REAGENT_CATALOGUE[reagent_id]["role"],
            }
            for reagent_id, quantity in rule["reagents"].items()
        ],
        "conditionsUsed": [
            {
                "id": reagent_id,
                "name": REAGENT_CATALOGUE[reagent_id]["name"],
                "role": REAGENT_CATALOGUE[reagent_id]["role"],
            }
            for reagent_id in rule.get("conditionsIds", [])
        ],
        "reactants": [
            {
                "canonicalSmiles": _canonical_smiles(Chem.RemoveHs(molecule)),
                "depictionSvg": render_2d_svg(Chem.RemoveHs(molecule)),
                **name_structure(Chem.RemoveHs(molecule)),
                "formula": rdMolDescriptors.CalcMolFormula(Chem.RemoveHs(molecule)),
                "atoms": [
                    {"element": atom.GetSymbol(), "origin": _origin(atom)}
                    for atom in molecule.GetAtoms()
                ],
            }
            for molecule in reactants
        ],
        "inputSpeciesIds": [item["speciesId"] for item in input_species],
        "inputMaterials": input_species,
        "reagentInputs": reagent_inputs,
        "productSpeciesIds": [product["speciesId"] for product in public_products],
        "products": public_products,
        "bondChanges": changes,
        "validation": {
            **balance,
            "productGraphsSanitized": True,
            "atomProvenanceComplete": all(
                "origin" in atom for product in products for atom in product["atoms"]
            ),
            "atomIndexMeaning": "Heavy-atom indices are zero-based in the canonical source SMILES graph; hydrogens are identified by their parent atom and per-parent ordinal.",
            "reactionFeasibility": "Limited to the stated substrate domain and rule conditions; this is not a prediction of experimental success.",
        },
        "evidence": {
            "classification": rule["classification"],
            "references": [REFERENCES[reference_id] for reference_id in rule["references"]],
            "limitations": rule["limitations"],
        },
    }


def _route_network(
    starting_materials: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """Serialize the actual material dependencies as a versioned reaction DAG."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    target_smiles = {item["canonicalSmiles"] for item in targets}

    def add_edge(source: str, destination: str, relation: str) -> None:
        if source not in nodes or destination not in nodes:
            raise PlannerInputError(
                "A route-network edge references an unknown species or reaction.",
                code="invalid_route_network",
                kind="internal",
            )
        edges.append({"from": source, "to": destination, "relation": relation})

    for material in starting_materials:
        for unit in range(1, material["quantity"] + 1):
            species_id = material["id"] if unit == 1 else f"{material['id']}-unit-{unit}"
            nodes[species_id] = {
                "id": species_id,
                "type": "species",
                "role": "target" if material["canonicalSmiles"] in target_smiles else "feedstock",
                "sourceType": "startingMaterial",
                "name": material.get("providedName") or material.get("name") or material["formula"],
                "formula": material["formula"],
                "canonicalSmiles": material["canonicalSmiles"],
                "depictionSvg": material["depictionSvg"],
                "quantity": 1,
                "isTarget": material["canonicalSmiles"] in target_smiles,
            }

    for step in steps:
        reaction_id = step["id"]
        nodes[reaction_id] = {
            "id": reaction_id,
            "type": "reaction",
            "role": "transformation",
            "step": step["step"],
            "reactionId": step["reactionId"],
            "name": step["name"],
            "conditions": step["conditions"],
            "evidence": step["evidence"],
            "inputSpeciesIds": [
                item["speciesId"] for item in step["inputMaterials"]
            ] + [item["speciesId"] for item in step["reagentInputs"]],
            "productSpeciesIds": step["productSpeciesIds"],
            "conditionIds": [item["id"] for item in step["conditionsUsed"]],
        }
        for material in step["inputMaterials"]:
            if material["speciesId"] not in nodes:
                raise PlannerInputError(
                    f"Route step {step['step']} consumes unavailable species {material['speciesId']!r}.",
                    code="invalid_route_network",
                    kind="internal",
                )
            add_edge(material["speciesId"], reaction_id, "consumed-by")
        for reagent in step["reagentInputs"]:
            nodes[reagent["speciesId"]] = {
                "id": reagent["speciesId"],
                "type": "species",
                "role": "reagent",
                "sourceType": "reagent",
                "name": reagent["name"],
                "formula": reagent["formula"],
                "canonicalSmiles": reagent["canonicalSmiles"],
                "quantity": reagent["quantity"],
                "isTarget": False,
            }
            add_edge(reagent["speciesId"], reaction_id, "reagent-input")
        for condition in step["conditionsUsed"]:
            condition_id = f"condition:{condition['id']}"
            nodes.setdefault(
                condition_id,
                {
                    "id": condition_id,
                    "type": "condition",
                    "role": condition["role"],
                    "name": condition["name"],
                    "isTarget": False,
                },
            )
            add_edge(condition_id, reaction_id, "condition")
        for product in step["products"]:
            is_target = product["canonicalSmiles"] in target_smiles
            nodes[product["speciesId"]] = {
                "id": product["speciesId"],
                "type": "species",
                "role": "target" if is_target else (
                    "coproduct" if product["role"] == "coproduct" else "intermediate"
                ),
                "sourceType": "reactionProduct",
                "name": product.get("providedName") or product.get("iupacName") or product["formula"],
                "formula": product["formula"],
                "canonicalSmiles": product["canonicalSmiles"],
                "depictionSvg": product["depictionSvg"],
                "quantity": 1,
                "isTarget": is_target,
                "atoms": product["atoms"],
            }
            add_edge(reaction_id, product["speciesId"], "produced")

    targets_remaining = Counter(
        item["canonicalSmiles"] for item in targets for _ in range(item["quantity"])
    )
    target_species_ids = []
    for species_id, node in nodes.items():
        if node.get("type") != "species" or not node.get("isTarget"):
            continue
        canonical = node["canonicalSmiles"]
        if targets_remaining[canonical] > 0:
            target_species_ids.append(species_id)
            targets_remaining[canonical] -= 1
    if any(targets_remaining.values()):
        raise PlannerInputError(
            "A successful route did not expose enough target species in its network.",
            code="invalid_route_network",
            kind="internal",
        )

    indegree = {node_id: 0 for node_id in nodes}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    consumed: Counter[str] = Counter()
    for edge in edges:
        outgoing[edge["from"]].append(edge["to"])
        indegree[edge["to"]] += 1
        if edge["relation"] == "consumed-by":
            consumed[edge["from"]] += 1
    for node_id, quantity in consumed.items():
        if quantity > nodes[node_id].get("quantity", 1):
            raise PlannerInputError(
                f"Route network consumes species {node_id!r} more than once.",
                code="invalid_route_network",
                kind="internal",
            )

    queue = [node_id for node_id, count in indegree.items() if count == 0]
    topological_order = []
    while queue:
        node_id = queue.pop()
        topological_order.append(node_id)
        for destination in outgoing[node_id]:
            indegree[destination] -= 1
            if indegree[destination] == 0:
                queue.append(destination)
    if len(topological_order) != len(nodes):
        raise PlannerInputError(
            "The reaction dependency graph contains a cycle.",
            code="invalid_route_network",
            kind="internal",
        )

    ancestors: dict[str, set[str]] = {}
    for node_id in topological_order:
        node = nodes[node_id]
        if node["type"] == "species" and node.get("sourceType") == "startingMaterial":
            ancestors[node_id] = {node_id}
        else:
            parents = [edge["from"] for edge in edges if edge["to"] == node_id]
            ancestors[node_id] = set().union(*(ancestors.get(parent, set()) for parent in parents))
        if node["type"] == "reaction":
            node["startingMaterialAncestors"] = sorted(ancestors[node_id])
            material_inputs = [
                edge["from"] for edge in edges
                if edge["to"] == node_id and edge["relation"] == "consumed-by"
            ]
            input_ancestry = [ancestors.get(parent, set()) for parent in material_inputs]
            node["convergent"] = (
                len(material_inputs) > 1
                and len(set().union(*input_ancestry)) > 1
            )

    return {
        "schemaVersion": "1.0.0",
        "type": "reaction-network-dag",
        "nodes": list(nodes.values()),
        "edges": edges,
        "inputSpeciesIds": [
            node_id for node_id, node in nodes.items()
            if node["type"] == "species" and node.get("sourceType") == "startingMaterial"
        ],
        "targetSpeciesIds": target_species_ids,
        "reactionOrder": [step["id"] for step in steps],
        "topologicalOrder": topological_order,
        "convergentReactionIds": [
            step["id"] for step in steps
            if nodes[step["id"]]["convergent"]
        ],
        "accounting": {
            "startingMaterialUnits": "Each input unit is a distinct node and may be consumed once.",
            "intermediateUnits": "Each generated molecular unit has a distinct node and may be consumed once.",
            "reagents": "Each atom-contributing stoichiometric reagent equivalent is a distinct node; listed catalysts/conditions are context nodes and are not atom sources.",
        },
    }


def _search(
    starting_materials: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    authorized_reagents: dict[str, int | None],
) -> dict[str, Any]:
    started_at = time.perf_counter()
    inventory: dict[InventoryKey, int] = {}
    for material in starting_materials:
        for unit in range(1, material["quantity"] + 1):
            source_id = material["id"] if unit == 1 else f"{material['id']}-unit-{unit}"
            source_name = material.get("name") or material["formula"]
            explicit = _explicit_source_molecule(
                material["canonicalSmiles"],
                "startingMaterial",
                source_id,
                source_name,
            )
            key = (
                material["canonicalSmiles"],
                source_id,
                source_name,
                json.dumps(
                    [_origin(atom) for atom in explicit.GetAtoms()],
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            )
            inventory[key] = 1

    sequence = itertools.count()
    initial_score = (0, 0, 0, ())
    queue = [
        (
            initial_score,
            next(sequence),
            inventory,
            authorized_reagents.copy(),
            Counter(),
            [],
        )
    ]
    visited = {_inventory_signature(inventory, authorized_reagents): initial_score}
    expanded = 0
    candidate_reactions = 0
    generated_states = 0
    duplicate_states = 0
    max_queue_size = len(queue)
    max_depth_reached = 0
    objective = (
        "minimum reaction steps, then minimum stoichiometric reagent equivalents, "
        "then minimum explicitly listed conditions"
    )
    while queue and expanded < MAX_SEARCH_STATES:
        score, _sequence, current_inventory, reagent_inventory, reagent_usage, steps = (
            heapq.heappop(queue)
        )
        signature = _inventory_signature(current_inventory, reagent_inventory)
        if visited.get(signature) != score:
            continue
        if _is_goal(current_inventory, targets):
            return {
                "status": "route-found",
                "route": steps,
                "reagentsUsed": [
                    {
                        "id": reagent_id,
                        "name": REAGENT_CATALOGUE[reagent_id]["name"],
                        "formula": REAGENT_CATALOGUE[reagent_id]["formula"],
                        "quantity": quantity,
                        "role": REAGENT_CATALOGUE[reagent_id]["role"],
                    }
                    for reagent_id, quantity in sorted(reagent_usage.items())
                ],
                "conditionsUsed": sorted(
                    {
                        condition_id
                        for step in steps
                        for condition_id in (
                            item["id"] for item in step["conditionsUsed"]
                        )
                    }
                ),
                "search": {
                    "algorithm": "bounded best-first forward search over supplied material and reagent inventories",
                    "objective": objective,
                    "maxDepth": MAX_SEARCH_DEPTH,
                    "maxExpandedStates": MAX_SEARCH_STATES,
                    "expandedStates": expanded,
                    "candidateReactions": candidate_reactions,
                    "generatedStates": generated_states,
                    "duplicateStates": duplicate_states,
                    "maxQueueSize": max_queue_size,
                    "maxDepthReached": max_depth_reached,
                    "elapsedMilliseconds": round(
                        (time.perf_counter() - started_at) * 1_000, 3
                    ),
                    "complete": True,
                    "optimalWithinModeledRules": True,
                },
            }
        expanded += 1
        if len(steps) >= MAX_SEARCH_DEPTH:
            continue

        for rule in RULES:
            if not _rule_reagents_available(rule, reagent_inventory):
                continue
            for selected in _candidate_substrate_sets(rule, current_inventory):
                candidate_reactions += 1
                generated_states += 1
                max_depth_reached = max(max_depth_reached, len(steps) + 1)
                next_inventory, materials = _materials_for_candidate(
                    rule, selected, current_inventory
                )
                products, changes, reactants, principal_products = _execute_rule(
                    rule, materials, len(steps) + 1
                )
                if not principal_products:
                    raise PlannerInputError(
                        f"Reaction rule {rule['id']} did not identify a principal product.",
                        code="invalid_reaction_rule",
                        kind="internal",
                    )
                step = _route_step(
                    rule,
                    products,
                    changes,
                    reactants,
                    materials,
                    len(steps) + 1,
                    principal_products,
                )
                _add_products_to_inventory(next_inventory, products, len(steps) + 1)
                next_reagents = _remaining_reagents(rule, reagent_inventory)
                next_usage = reagent_usage.copy()
                for reagent_id, quantity in rule["reagents"].items():
                    next_usage[reagent_id] += quantity
                next_score = (
                    score[0] + 1,
                    score[1] + sum(rule["reagents"].values()),
                    score[2] + len(rule.get("conditionsIds", [])),
                    score[3] + (rule["id"],),
                )
                next_signature = _inventory_signature(next_inventory, next_reagents)
                if next_signature in visited and visited[next_signature] <= next_score:
                    duplicate_states += 1
                    continue
                visited[next_signature] = next_score
                heapq.heappush(
                    queue,
                    (
                        next_score,
                        next(sequence),
                        next_inventory,
                        next_reagents,
                        next_usage,
                        [*steps, step],
                    ),
                )
                max_queue_size = max(max_queue_size, len(queue))

    complete = not queue
    return {
        "status": "no-supported-route" if complete else "search-limit-reached",
        "route": [],
        "search": {
            "algorithm": "bounded best-first forward search over supplied material and reagent inventories",
            "objective": objective,
            "maxDepth": MAX_SEARCH_DEPTH,
            "maxExpandedStates": MAX_SEARCH_STATES,
            "expandedStates": expanded,
            "candidateReactions": candidate_reactions,
            "generatedStates": generated_states,
            "duplicateStates": duplicate_states,
            "maxQueueSize": max_queue_size,
            "maxDepthReached": max_depth_reached,
            "elapsedMilliseconds": round(
                (time.perf_counter() - started_at) * 1_000, 3
            ),
            "complete": complete,
            "optimalWithinModeledRules": complete,
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
        payload, "startingMaterials", must_be_organic=False
    )
    targets = _compound_entries(payload, "targetProducts", must_be_organic=True)
    reagent_mode = payload.get("reagentMode", "manual")
    if not isinstance(reagent_mode, str) or reagent_mode not in {"manual", "auto"}:
        raise PlannerInputError("reagentMode must be 'manual' or 'auto'.")
    requested_reagents = _reagent_inventory(payload)
    reagent_inventory = (
        {reagent_id: None for reagent_id in REAGENT_CATALOGUE}
        if reagent_mode == "auto"
        else requested_reagents
    )
    result = _search(starting_materials, targets, reagent_inventory)
    if result["status"] == "route-found":
        result["routeNetwork"] = _route_network(
            starting_materials, targets, result["route"]
        )
    if reagent_mode == "auto" and result["status"] == "route-found":
        authorized_reagents = result["reagentsUsed"]
    else:
        authorized_reagents = [
            {
                "id": reagent_id,
                "name": REAGENT_CATALOGUE[reagent_id]["name"],
                "formula": REAGENT_CATALOGUE[reagent_id]["formula"],
                "quantity": quantity,
                "role": REAGENT_CATALOGUE[reagent_id]["role"],
            }
            for reagent_id, quantity in sorted(requested_reagents.items())
        ]
    result.update(
        {
            "knowledgeBase": {
                "name": "AtomView curated organic reaction exemplars",
                "rules": [
                    {
                        "id": rule["id"],
                        "name": rule["name"],
                        "classification": rule["classification"],
                        "references": [
                            REFERENCES[reference_id]
                            for reference_id in rule["references"]
                        ],
                    }
                    for rule in RULES
                ],
                "notComprehensive": True,
            },
            "startingMaterials": starting_materials,
            "targetProducts": targets,
            "authorizedReagents": authorized_reagents,
            "reagentMode": reagent_mode,
            "interpretation": (
                "A route is an atom- and charge-balanced application of a constrained, "
                "evidence-listed rule. Route optimality is limited to this rule set, the "
                "supplied materials, the selected reagent mode, and configured search limits. "
                "It is not a yield, kinetic, thermodynamic, selectivity, or experimental-success prediction."
            ),
        }
    )
    return result


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, body: dict[str, Any]) -> None:
        request_id = getattr(self, "_atomview_request_id", None)
        if request_id is None:
            request_id = uuid.uuid4().hex
            self._atomview_request_id = request_id
        response_body = {**body, "requestId": request_id}
        encoded = json.dumps(
            response_body, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Request-ID", request_id)
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        self._atomview_request_id = uuid.uuid4().hex
        self._send_json(
            200,
            {
                "status": "ready",
                "engine": "AtomView curated forward synthesis search",
                "version": _build_identity(),
                "reactionRules": [
                    {
                        "id": rule["id"],
                        "name": rule["name"],
                        "family": rule["family"],
                        "classification": rule["classification"],
                        "substrates": list(rule["substrates"]),
                        "reagents": rule["reagents"],
                        "conditionsIds": rule.get("conditionsIds", []),
                        "references": [
                            REFERENCES[reference_id]
                            for reference_id in rule["references"]
                        ],
                        "limitations": rule["limitations"],
                    }
                    for rule in RULES
                ],
                "reagentCatalogue": [
                    {"id": reagent_id, **reagent}
                    for reagent_id, reagent in REAGENT_CATALOGUE.items()
                ],
                "limits": {
                    "maxDepth": MAX_SEARCH_DEPTH,
                    "maxExpandedStates": MAX_SEARCH_STATES,
                },
            },
        )

    def do_POST(self) -> None:
        self._atomview_request_id = uuid.uuid4().hex
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_error(
                400, "invalid_request", "Invalid Content-Length header.", "user-input"
            )
            return
        if content_length <= 0:
            self._send_error(
                400, "missing_request_body", "A JSON request body is required.", "user-input"
            )
            return
        if content_length > MAX_REQUEST_BYTES:
            self._send_error(
                413,
                "request_too_large",
                "Request body exceeds the 1 MB limit.",
                "user-input",
            )
            return
        try:
            payload = json.loads(self.rfile.read(content_length))
            result = plan_synthesis(payload)
            if result["status"] == "no-supported-route":
                self._send_error(
                    422,
                    "unsupported_chemistry",
                    result["message"],
                    "unsupported-chemistry",
                    diagnostics=result["search"],
                )
                return
            if result["status"] == "search-limit-reached":
                self._send_error(
                    422,
                    "search_limit_reached",
                    result["message"],
                    "search-limit",
                    diagnostics=result["search"],
                )
                return
            self._send_json(200, result)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_error(
                400, "invalid_json", "Request body must be valid JSON.", "user-input"
            )
        except (PlannerInputError, GeometryInputError) as error:
            code = getattr(error, "code", "invalid_structure")
            kind = getattr(error, "kind", "invalid-structure")
            self._send_error(422, code, str(error), kind)
        except Exception as error:
            _LOGGER.exception(
                "Reaction planning failed request_id=%s",
                self._atomview_request_id,
                exc_info=error,
            )
            self._send_error(
                500,
                "internal_error",
                "The reaction planner could not complete this request.",
                "internal",
            )

    def _send_error(
        self,
        status_code: int,
        code: str,
        message: str,
        kind: str,
        **extra: Any,
    ) -> None:
        self._send_json(
            status_code,
            {
                "error": {
                    "code": code,
                    "message": message,
                    "kind": kind,
                    **extra,
                }
            },
        )

    def log_message(self, format: str, *args: Any) -> None:
        print(f"Reaction planner API: {format % args}")
