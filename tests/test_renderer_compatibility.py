import math
import unittest

from rdkit import Chem

from api.geometry import generate_geometry
from renderer_compatibility_corpus import RENDERER_COMPATIBILITY_CORPUS


class RendererCompatibilityCorpusTests(unittest.TestCase):
    def test_curated_chemical_diversity_corpus_preserves_identity_and_generates_geometry(self):
        self.assertGreaterEqual(len(RENDERER_COMPATIBILITY_CORPUS), 150)
        expected_ids = {case.case_id for case in RENDERER_COMPATIBILITY_CORPUS}
        self.assertEqual(len(expected_ids), len(RENDERER_COMPATIBILITY_CORPUS))

        for case in RENDERER_COMPATIBILITY_CORPUS:
            with self.subTest(case_id=case.case_id, category=case.category):
                source = Chem.MolFromSmiles(case.smiles)
                expected_with_hydrogens = Chem.AddHs(source)
                result = generate_geometry(
                    {"smiles": case.smiles, "conformers": 1}
                )
                metadata = result["metadata"]

                self.assertEqual(metadata["canonicalSmiles"], case.expected_smiles)
                self.assertEqual(metadata["formula"], case.expected_formula)
                self.assertEqual(metadata["formalCharge"], case.expected_charge)
                self.assertEqual(
                    sum(atom["atomicNumber"] > 1 for atom in result["atoms"]),
                    case.expected_heavy_atoms,
                )
                self.assertEqual(
                    len(result["atoms"]), expected_with_hydrogens.GetNumAtoms()
                )
                self.assertEqual(
                    len(result["bonds"]), expected_with_hydrogens.GetNumBonds()
                )
                self.assertEqual(
                    [
                        (center["atomIndex"], center["label"])
                        for center in metadata["stereochemistry"]
                    ],
                    list(case.expected_stereochemistry),
                )
                self.assertIn(metadata["forceField"], ("MMFF94s", "UFF"))
                self.assertIn("<svg", result["depictionSvg"])
                self.assertTrue(
                    all(
                        math.isfinite(value)
                        for atom in result["atoms"]
                        for value in atom["position"].values()
                    )
                )
                for bond in result["bonds"]:
                    start = result["atoms"][bond["from"]]["position"]
                    end = result["atoms"][bond["to"]]["position"]
                    distance = math.dist(
                        [start[axis] for axis in ("x", "y", "z")],
                        [end[axis] for axis in ("x", "y", "z")],
                    )
                    self.assertGreater(distance, 0.1)
                    self.assertLess(distance, 3.5)


if __name__ == "__main__":
    unittest.main()
