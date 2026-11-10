import sys
import types
import unittest
from unittest.mock import patch

from api.geometry import Chem
from api.structure_naming import _name_canonical_smiles, name_structure


class StructureNamingTests(unittest.TestCase):
    def setUp(self):
        _name_canonical_smiles.cache_clear()
        patcher = patch("api.structure_naming._ENGINE", None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.orthonym = types.ModuleType("orthonym")
        self.orthonym.__path__ = []
        self.orthonym.Orthonym = type("Orthonym", (), {})
        self.orthonym.OrthonymLimitError = type("OrthonymLimitError", (Exception,), {})
        self.jars = types.ModuleType("orthonym.jars")
        self.jars.JarUnavailable = type("JarUnavailable", (Exception,), {})
        self.modules = patch.dict(
            sys.modules,
            {"orthonym": self.orthonym, "orthonym.jars": self.jars},
        )
        self.modules.start()
        patcher = patch("api.structure_naming._configure_local_engine")
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.modules.stop()
        _name_canonical_smiles.cache_clear()

    def test_opsin_round_trip_accepts_only_exact_isomeric_structure(self):
        self.orthonym.Orthonym = type(
            "Orthonym",
            (),
            {
                "name_tiered": lambda self, smiles: {
                    "name": "ethanol",
                    "tier": "pin_verified",
                    "verified": "opsin",
                }
            },
        )

        result = name_structure(Chem.MolFromSmiles("CCO"))

        self.assertEqual(result["iupacName"], "ethanol")
        self.assertEqual(result["naming"]["status"], "verified")
        self.assertIn("canonical isomeric SMILES identity", result["naming"]["verification"])

    def test_round_trip_mismatch_is_rejected(self):
        self.orthonym.Orthonym = type(
            "Orthonym",
            (),
            {
                "name_tiered": lambda self, smiles: {
                    "name": "propan-1-ol",
                    "tier": "pin_verified",
                    "verified": "opsin",
                }
            },
        )

        result = name_structure(Chem.MolFromSmiles("CCO"))

        self.assertIsNone(result["iupacName"])
        self.assertEqual(result["naming"]["status"], "unavailable")
        self.assertEqual(result["naming"]["reason"], "opsin-round-trip-identity-mismatch")

    def test_best_effort_name_is_not_exposed_as_verified_iupac(self):
        self.orthonym.Orthonym = type(
            "Orthonym",
            (),
            {
                "name_tiered": lambda self, smiles: {
                    "name": "example candidate",
                    "tier": "best_effort",
                    "verified": None,
                }
            },
        )

        result = name_structure(Chem.MolFromSmiles("CCO"))

        self.assertIsNone(result["iupacName"])
        self.assertEqual(result["naming"]["status"], "unverified")
        self.assertIn("not verified", result["name"])


if __name__ == "__main__":
    unittest.main()
