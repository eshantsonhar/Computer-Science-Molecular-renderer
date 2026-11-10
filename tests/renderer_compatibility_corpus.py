from dataclasses import dataclass

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors


@dataclass(frozen=True)
class MoleculeCase:
    case_id: str
    category: str
    smiles: str
    expected_smiles: str
    expected_formula: str
    expected_charge: int
    expected_heavy_atoms: int
    expected_stereochemistry: tuple[tuple[int, str], ...]


CASE_GROUPS = {
    "alkanes": tuple("C" * count for count in range(1, 21))
    + (
        "CC(C)C",
        "CC(C)CC",
        "CC(C)(C)C",
        "CC(C)C(C)C",
        "CCC(C)CC",
        "CC(C)CCC",
        "CC(C)(C)CC",
        "CCC(C)(C)C",
        "CC(C)CC(C)C",
        "CC(C)(CC)CC",
        "CC(C)C(C)(C)C",
        "CC(C)CC(C)CC",
    ),
    "alkenes": (
        "C=C",
        "C=CC",
        "C=CCC",
        "C=CCCC",
        "C=CCCCC",
        "C=CCCCCC",
        "CC=CC",
        "C/C=C/C",
        "C/C=C\\C",
        "C=CC=C",
        "CC(C)=C",
        "C=C(C)CC",
        "C1CC=CCC1",
        "C1=CCCCC1",
    ),
    "alkynes": (
        "C#C",
        "C#CC",
        "C#CCC",
        "C#CCCC",
        "C#CCCCC",
        "CC#CC",
        "CC#CCC",
        "C#CC#C",
    ),
    "cyclic_polycyclic": (
        "C1CC1",
        "C1CCC1",
        "C1CCCC1",
        "C1CCCCC1",
        "C1CCCCCC1",
        "C1CCCCCCCC1",
        "C1CCCCCCCCCCC1",
        "C1CC2CCC1C2",
        "C1CCC2CCCCC2C1",
        "C1CC2CCC3CCCCC3C2C1",
    ),
    "functional_groups": (
        "CCO",
        "CCCCO",
        "CC(C)O",
        "COC",
        "CCOC",
        "CC=O",
        "CCC=O",
        "CC(=O)C",
        "CC(=O)CC",
        "CC(=O)O",
        "CCC(=O)O",
        "CCOC(=O)C",
        "CC(=O)N",
        "CCC(=O)N",
        "CCN",
        "CCCN",
        "CC#N",
        "CCCl",
        "CCBr",
        "CCI",
        "CCF",
        "C[N+](=O)[O-]",
        "CCS",
        "CC(=O)S",
        "CS(C)=O",
        "CS(=O)(=O)C",
        "O=C1CCCCC1",
        "C1CO1",
        "C1CCOC1",
        "C1CCNC1",
    ),
    "aromatic_heterocyclic": (
        "c1ccccc1",
        "Cc1ccccc1",
        "Oc1ccccc1",
        "Nc1ccccc1",
        "O=[N+]([O-])c1ccccc1",
        "Clc1ccccc1",
        "Brc1ccccc1",
        "Ic1ccccc1",
        "c1ccc(cc1)C(=O)O",
        "c1ccc(cc1)C(=O)N",
        "c1ccc2ccccc2c1",
        "c1ccc2cc3ccccc3cc2c1",
        "c1ccncc1",
        "c1ccoc1",
        "c1ccsc1",
        "c1cc[nH]c1",
        "c1ncc[nH]1",
        "c1ccc2[nH]ccc2c1",
        "c1ccc2ncccc2c1",
        "c1nc2ccccc2[nH]1",
        "c1ncnc2[nH]cnc12",
        "c1ncc2ncnc2[nH]1",
        "c1cncnc1",
        "c1cnccn1",
        "c1cccnn1",
        "c1ncn[nH]1",
        "c1nn[nH]c1",
        "c1ocnc1",
        "c1scnc1",
        "c1ccc2occc2c1",
        "c1ccc2sccc2c1",
        "c1ccc2ncncc2c1",
        "c1ccc2nccnc2c1",
        "O=c1cc[nH]c(=O)[nH]1",
        "CC1=CNC(=O)NC1=O",
        "Cn1c(=O)c2c(ncn2C)n(C)c1=O",
    ),
    "organophosphorus": (
        "CP(C)C",
        "CP(=O)(C)C",
        "COP(=O)(OC)OC",
        "CCP(=O)(O)O",
        "COP(=O)(N)OC",
        "OP(=O)(O)OP(=O)(O)O",
        "OP(=O)(O)OP(=O)(O)OP(=O)(O)O",
        "CCP(=O)(O)OC",
        "CCP(=O)(OC)OC",
        "CCP(=O)(O)N",
        "CCOP(=O)(O)O",
        "CCOP(=O)(O)OP(=O)(O)O",
        "CCP(=O)([O-])[O-]",
        "CP(=O)([O-])([O-])",
        "NCCOP(=O)(O)O",
        "c1ccccc1P(=O)(O)O",
        "c1ccccc1P(O)O",
        "CCOP(=O)(N)O",
        "COP(OC)(O)=O",
        "CCOP(=O)(OC)OC",
        "O=P(O)(O)N",
        "COP(=O)(N)O",
        "CCOP(=O)(N)N",
        "CCP(=O)(O)OCC",
        "CCP(=O)(O)NCC",
        "P(=O)(O)(O)O",
        "OP(=S)(O)O",
        "CP(=S)(O)O",
        "COP(=S)(OC)OC",
        "C=CP(=O)(O)O",
        "C1COP(=O)(O)O1",
        "NCP(=O)(O)O",
        "OP(=O)([O-])OP(=O)([O-])[O-]",
        "OP(=O)([O-])OP(=O)([O-])OP(=O)([O-])[O-]",
        "CCP(=O)([O-])OCC",
        "CP(=O)(O)N",
        "CCP(=S)(O)O",
        "Nc1ncnc2c1ncn2[C@@H]1O[C@H](COP(=O)([O-])OP(=O)"
        "([O-])OP(=O)([O-])[O-])[C@@H](O)[C@H]1O",
    ),
    "unusual_elements": (
        "OB(O)c1ccccc1",
        "C[Si](C)(C)C",
        "C[Se]C",
        "C[Se](=O)C",
        "C[Te]C",
        "B(O)(O)C",
        "C[Si](C)(C)CC",
        "CC[Se]CC",
        "CC[As](C)C",
        "CC[Ge](C)C",
        "CC[Sn](C)(C)C",
        "CCP(C)(C)C",
        "FC(F)(F)C",
        "CBr",
        "CI",
        "C[Mg]Br",
    ),
    "charged": (
        "[NH4+]",
        "C[NH3+]",
        "[O-]C=O",
        "CC(=O)[O-]",
        "[NH3+]CC(=O)[O-]",
        "[N+](C)(C)(C)C",
        "[O-][N+](=O)c1ccccc1",
        "C[N+](=O)[O-]",
        "[NH3+]CC(=O)O",
        "CC(=O)[O-].[Na+]",
        "[Cl-]",
        "[K+]",
        "CC(=O)[O-].[NH4+]",
        "CCP(=O)([O-])[O-]",
        "Nc1ncc[nH]1",
        "[NH2+]1CCCCC1",
    ),
    "stereochemical_biochemical": (
        "C[C@H](O)C(=O)O",
        "C[C@@H](N)C(=O)O",
        "N[C@@H](C)C(=O)O",
        "C[C@H](O)[C@@H](O)C",
        "C[C@H](F)C(=O)O",
        "C/C=C/C",
        "C/C=C\\C",
        "N[C@@H](CC(=O)O)C(=O)O",
        "C[C@H]1CCCCC1",
        "C1CC[C@H](O)CC1",
        "N[C@@H](CC1=CC=CC=C1)C(=O)O",
        "CC(=O)N[C@@H](C)C(=O)O",
        "NCC(=O)NCC(=O)O",
        "Nc1ncnc2c1ncn2[C@@H]1O[C@H](CO)[C@@H](O)[C@H]1O",
        "Nc1ncnc2c1ncn2[C@@H]1O[C@H](COP(=O)(O)O)[C@@H](O)[C@H]1O",
        "Nc1ncnc2c1ncn2[C@@H]1O[C@H](COP(=O)(O)OP(=O)(O)O)[C@@H](O)[C@H]1O",
        "Nc1ncnc2c1ncn2[C@@H]1O[C@H](COP(=O)(O)OP(=O)(O)OP(=O)(O)O)[C@@H](O)[C@H]1O",
        "CC(C)Cc1ccc(cc1)[C@@H](C)C(=O)O",
        "CC(=O)Oc1ccccc1C(=O)O",
        "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@H]1O",
        "C[C@H](O)C(=O)O",
        "N[C@@H](CC1=CN=CN1)C(=O)O",
        "N[C@@H](CCSC)C(=O)O",
        "N[C@@H](CC(=O)O)C(=O)O",
        "N[C@@H](CC(=O)N)C(=O)O",
        "N[C@@H](CC1=CC=CC=C1)C(=O)O",
        "N[C@@H](CC(=O)O)C(=O)NCC(=O)O",
        "Nc1ncnc2c1ncn2[C@@H]1O[C@H](CO)[C@@H](O)[C@H]1O",
        "Nc1ncnc2c1ncn2[C@@H]1O[C@H](COP(=O)(O)O)[C@@H](O)[C@H]1O",
    ),
    "heavier_heteroatoms": (
        "C[Se](=O)(C)C",
        "C[Si](C)(C)O",
        "C[Ge](C)(C)C",
        "Brc1ccc(Br)cc1",
        "FC(F)(F)C(F)(F)F",
        "C[As](=O)(C)C",
        "CC[Sn](C)(C)C",
        "C[Te](C)=O",
    ),
}


def build_corpus() -> tuple[MoleculeCase, ...]:
    cases = []
    seen = set()
    for category, structures in CASE_GROUPS.items():
        category_index = 0
        for smiles in structures:
            molecule = Chem.MolFromSmiles(smiles)
            if molecule is None:
                raise ValueError(f"Invalid curated SMILES in {category}: {smiles}")
            canonical = Chem.MolToSmiles(
                molecule, canonical=True, isomericSmiles=True
            )
            if canonical in seen:
                continue
            seen.add(canonical)
            category_index += 1
            stereochemistry = tuple(
                (index, label)
                for index, label in Chem.FindMolChiralCenters(
                    molecule, includeUnassigned=True, includeCIP=True
                )
                if label != "?"
            )
            cases.append(
                MoleculeCase(
                    case_id=f"{category}-{category_index:03d}",
                    category=category,
                    smiles=smiles,
                    expected_smiles=canonical,
                    expected_formula=rdMolDescriptors.CalcMolFormula(molecule),
                    expected_charge=Chem.GetFormalCharge(molecule),
                    expected_heavy_atoms=molecule.GetNumHeavyAtoms(),
                    expected_stereochemistry=stereochemistry,
                )
            )
    return tuple(cases)


RENDERER_COMPATIBILITY_CORPUS = build_corpus()
