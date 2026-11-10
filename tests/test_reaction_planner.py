import json
import subprocess
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from pathlib import Path
from unittest.mock import patch

from chemistry.reaction_planner import PlannerInputError, plan_synthesis
from chemistry.reaction_planner import handler as reaction_handler


class ReactionPlanningTests(unittest.TestCase):
    def test_acetyl_chloride_ammonolysis_balances_every_atom_and_charge(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "acetyl-chloride", "name": "ethanoyl chloride", "smiles": "CC(=O)Cl"}
                ],
                "targetProducts": [{"id": "acetamide", "smiles": "CC(N)=O"}],
                "reagents": {"ammonia": 2},
            }
        )

        self.assertEqual(result["status"], "route-found")
        self.assertEqual(len(result["route"]), 1)
        step = result["route"][0]
        self.assertEqual(step["reactionId"], "acyl-chloride-ammonolysis")
        self.assertIn("Ammonia replaces", step["shortDescription"])
        products = {product["formula"]: product for product in step["products"]}
        self.assertEqual(products["C2H5NO"]["canonicalSmiles"], "CC(N)=O")
        self.assertIn("<svg", products["C2H5NO"]["depictionSvg"])
        self.assertIn("<svg", step["reactants"][0]["depictionSvg"])
        self.assertIn("Cl-", products)
        self.assertIn("H4N+", products)
        self.assertTrue(step["validation"]["atomBalanceChecked"])
        self.assertTrue(step["validation"]["chargeBalanceChecked"])
        self.assertTrue(step["validation"]["productGraphsSanitized"])
        self.assertTrue(step["validation"]["atomProvenanceComplete"])
        self.assertEqual(
            step["validation"]["reactantAtomCounts"],
            step["validation"]["productAtomCounts"],
        )
        nitrogen_origins = [
            atom["origin"]
            for product in step["products"]
            for atom in product["atoms"]
            if atom["element"] == "N"
        ]
        self.assertEqual(
            {origin["sourceType"] for origin in nitrogen_origins}, {"reagent"}
        )
        self.assertEqual(
            {origin["sourceId"] for origin in nitrogen_origins},
            {
                "ammonia-step-1-equivalent-1",
                "ammonia-step-1-equivalent-2",
            },
        )

    def test_ethanolysis_accounts_for_organic_atom_donor_and_hcl(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "acetyl-chloride", "smiles": "CC(=O)Cl"},
                    {"id": "ethanol", "smiles": "CCO"},
                ],
                "targetProducts": [{"id": "ethyl-acetate", "smiles": "CCOC(C)=O"}],
            }
        )

        step = result["route"][0]
        products = {product["formula"]: product for product in step["products"]}
        ester = products["C4H8O2"]
        hydrogen_chloride = products["HCl"]
        self.assertEqual(ester["canonicalSmiles"], "CCOC(C)=O")
        self.assertEqual(
            {atom["origin"]["sourceId"] for atom in ester["atoms"] if atom["element"] == "C"},
            {"acetyl-chloride", "ethanol"},
        )
        self.assertEqual(
            next(atom for atom in hydrogen_chloride["atoms"] if atom["element"] == "H")[
                "origin"
            ]["sourceId"],
            "ethanol",
        )
        self.assertTrue(step["validation"]["atomBalanceChecked"])
        self.assertTrue(step["validation"]["chargeBalanceChecked"])

    def test_every_curated_reaction_rule_executes_with_balanced_products(self):
        examples = [
            (
                "acyl-chloride-ammonolysis",
                [("acyl", "CC(=O)Cl", 1)],
                "CC(N)=O",
                1,
            ),
            (
                "acyl-chloride-aminolysis",
                [("acyl", "CC(=O)Cl", 1), ("methylamine", "CN", 2)],
                "CNC(C)=O",
                1,
            ),
            (
                "acyl-chloride-alcoholysis",
                [("acyl", "CC(=O)Cl", 1), ("ethanol", "CCO", 1)],
                "CCOC(C)=O",
                1,
            ),
            (
                "acyl-chloride-hydrolysis",
                [("acyl", "CC(=O)Cl", 1)],
                "CC(=O)O",
                1,
            ),
            (
                "acyl-chloride-anhydride-formation",
                [("acyl", "CC(=O)Cl", 1), ("acetate", "CC(=O)[O-]", 1)],
                "CC(=O)OC(C)=O",
                1,
            ),
            (
                "acid-chloride-formation",
                [("acid", "CC(=O)O", 1)],
                "CC(=O)Cl",
                1,
            ),
            (
                "ester-saponification",
                [("ester", "CCOC(C)=O", 1)],
                "CC(=O)[O-]",
                1,
            ),
            (
                "carboxylate-acidification",
                [("acetate", "CC(=O)[O-].[Na+]", 1)],
                "CC(=O)O",
                1,
            ),
            ("alkene-hydrogenation", [("alkene", "C=CCC", 1)], "CCCC", 1),
            ("alkyne-hydrogenation", [("alkyne", "C#CCC", 1)], "CCCC", 1),
            ("reductive-alkene-ozonolysis", [("alkene", "CC=CC", 1)], "CC=O", 2),
            ("peroxide-hbr-addition", [("alkene", "C=CCC", 1)], "CCCCBr", 1),
        ]
        for reaction_id, materials, target, target_quantity in examples:
            with self.subTest(reaction_id=reaction_id):
                result = plan_synthesis(
                    {
                        "startingMaterials": [
                            {"id": name, "smiles": smiles, "quantity": quantity}
                            for name, smiles, quantity in materials
                        ],
                        "targetProducts": [
                            {
                                "id": "target",
                                "smiles": target,
                                "quantity": target_quantity,
                            }
                        ],
                        "reagentMode": "auto",
                    }
                )
                self.assertEqual(result["status"], "route-found")
                self.assertEqual(len(result["route"]), 1)
                step = result["route"][0]
                self.assertEqual(step["reactionId"], reaction_id)
                self.assertTrue(step["validation"]["atomBalanceChecked"])
                self.assertTrue(step["validation"]["chargeBalanceChecked"])
                self.assertTrue(step["validation"]["atomProvenanceComplete"])
                self.assertTrue(step["evidence"]["references"])
                self.assertTrue(
                    all("<svg" in product["depictionSvg"] for product in step["products"])
                )

    def test_multi_step_route_consumes_only_authorized_stoichiometric_reagents(self):
        result = plan_synthesis(
            {
                "startingMaterials": [{"id": "acid", "smiles": "CC(=O)O"}],
                "targetProducts": [{"id": "amide", "smiles": "CC(N)=O"}],
                "reagents": {"thionyl-chloride": 1, "ammonia": 2},
            }
        )

        self.assertEqual(result["status"], "route-found")
        self.assertEqual(
            [step["reactionId"] for step in result["route"]],
            ["acid-chloride-formation", "acyl-chloride-ammonolysis"],
        )
        self.assertEqual(
            {item["id"]: item["quantity"] for item in result["reagentsUsed"]},
            {"ammonia": 2, "thionyl-chloride": 1},
        )

    def test_manual_hydrogenation_requires_the_listed_catalyst(self):
        result = plan_synthesis(
            {
                "startingMaterials": [{"id": "alkene", "smiles": "C=CCC"}],
                "targetProducts": [{"id": "alkane", "smiles": "CCCC"}],
                "reagents": {"hydrogen": 1},
            }
        )
        self.assertEqual(result["status"], "no-supported-route")

    def test_manual_hydrogenation_accepts_only_selected_hydrogen_and_catalyst(self):
        result = plan_synthesis(
            {
                "startingMaterials": [{"id": "alkene", "smiles": "C=CCC"}],
                "targetProducts": [{"id": "alkane", "smiles": "CCCC"}],
                "reagents": {"hydrogen": 1, "palladium-carbon": 1},
            }
        )

        self.assertEqual(result["status"], "route-found")
        self.assertEqual(result["reagentsUsed"][0]["id"], "hydrogen")
        self.assertEqual(
            result["route"][0]["conditionsUsed"][0]["id"],
            "palladium-carbon",
        )

    def test_multi_product_search_respects_starting_material_and_reagent_quantities(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "acetyl-chloride", "smiles": "CC(=O)Cl", "quantity": 2},
                    {"id": "ethanol", "smiles": "CCO", "quantity": 1},
                ],
                "targetProducts": [
                    {"id": "acetamide", "smiles": "CC(N)=O"},
                    {"id": "ethyl-acetate", "smiles": "CCOC(C)=O"},
                ],
                "reagents": {"ammonia": 2},
            }
        )

        self.assertEqual(result["status"], "route-found")
        self.assertEqual(
            [step["reactionId"] for step in result["route"]],
            ["acyl-chloride-alcoholysis", "acyl-chloride-ammonolysis"],
        )
        self.assertIn("minimum reaction steps", result["search"]["objective"])

    def test_auto_mode_selects_only_reagent_required_by_target(self):
        amide_route = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "acid-chloride", "smiles": "CC(=O)Cl"}
                ],
                "targetProducts": [{"id": "amide", "smiles": "CC(N)=O"}],
                "reagentMode": "auto",
                "reagents": {"ammonia": 0},
            }
        )
        self.assertEqual(amide_route["status"], "route-found")
        self.assertEqual(amide_route["reagentMode"], "auto")
        self.assertEqual(
            amide_route["authorizedReagents"],
            [
                {
                    "id": "ammonia",
                    "name": "Ammonia",
                    "formula": "NH3",
                    "quantity": 2,
                    "role": "stoichiometric nucleophile",
                }
            ],
        )

        ester_route = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "acid-chloride", "smiles": "CC(=O)Cl"},
                    {"id": "ethanol", "smiles": "CCO"},
                ],
                "targetProducts": [{"id": "ester", "smiles": "CCOC(C)=O"}],
                "reagentMode": "auto",
                "reagents": {"ammonia": 0},
            }
        )
        self.assertEqual(ester_route["status"], "route-found")
        self.assertEqual(ester_route["authorizedReagents"], [])
        self.assertEqual(ester_route["reagentsUsed"], [])

    def test_auto_mode_does_not_authorize_unneeded_ammonia(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "acid-chloride", "smiles": "CC(=O)Cl"}
                ],
                "targetProducts": [{"id": "already-present", "smiles": "CC(=O)Cl"}],
                "reagentMode": "auto",
            }
        )
        self.assertEqual(result["status"], "route-found")
        self.assertEqual(result["authorizedReagents"], [])

    def test_unknown_reagent_mode_is_rejected(self):
        with self.assertRaises(PlannerInputError):
            plan_synthesis(
                {
                    "startingMaterials": [{"id": "acid", "smiles": "CC(=O)Cl"}],
                    "targetProducts": [{"id": "amide", "smiles": "CC(N)=O"}],
                    "reagentMode": "guess",
                }
            )

    def test_search_supports_routes_longer_than_three_steps(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "acetyl-chloride", "smiles": "CC(=O)Cl", "quantity": 4}
                ],
                "targetProducts": [
                    {"id": f"acetamide-{index}", "smiles": "CC(N)=O"}
                    for index in range(4)
                ],
                "reagents": {"ammonia": 8},
            }
        )

        self.assertEqual(result["status"], "route-found")
        self.assertEqual(len(result["route"]), 4)
        self.assertEqual(result["search"]["maxDepth"], 20)

    def test_no_route_is_distinguished_from_global_chemical_impossibility(self):
        result = plan_synthesis(
            {
                "startingMaterials": [{"id": "acetyl-chloride", "smiles": "CC(=O)Cl"}],
                "targetProducts": [{"id": "acetamide", "smiles": "CC(N)=O"}],
            }
        )

        self.assertEqual(result["status"], "no-supported-route")
        self.assertIn("does not establish", result["message"])

    def test_acyl_chloride_scope_abstains_for_unmodeled_heteroatom_substituents(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "fluoro-acid-chloride", "smiles": "CC(F)C(=O)Cl"}
                ],
                "targetProducts": [{"id": "fluoro-amide", "smiles": "CC(F)C(N)=O"}],
                "reagents": {"ammonia": 2},
            }
        )

        self.assertEqual(result["status"], "no-supported-route")
        self.assertEqual(result["route"], [])

    def test_multiple_target_quantities_are_added_not_overwritten(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "acetyl-chloride", "smiles": "CC(=O)Cl"}
                ],
                "targetProducts": [
                    {"id": "acetamide-one", "smiles": "CC(N)=O"},
                    {"id": "acetamide-two", "smiles": "CC(N)=O"},
                ],
                "reagents": {"ammonia": 2},
            }
        )

        self.assertEqual(result["status"], "no-supported-route")

    def test_invalid_or_nonorganic_inputs_are_rejected(self):
        invalid_cases = (
            {
                "startingMaterials": [{"id": "water", "smiles": "O"}],
                "targetProducts": [{"id": "acetamide", "smiles": "CC(N)=O"}],
            },
            {
                "startingMaterials": [{"id": "bad", "smiles": "C1("}],
                "targetProducts": [{"id": "acetamide", "smiles": "CC(N)=O"}],
            },
            {
                "startingMaterials": [
                    {"id": "acetyl-chloride", "smiles": "CC(=O)Cl", "quantity": True}
                ],
                "targetProducts": [{"id": "acetamide", "smiles": "CC(N)=O"}],
            },
        )
        for payload in invalid_cases:
            with self.subTest(payload=payload):
                with self.assertRaises(PlannerInputError):
                    plan_synthesis(payload)


class ReactionPlannerHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), reaction_handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_get_reports_local_rule_set_and_bounds(self):
        with urlopen(self.base_url, timeout=2) as response:
            body = json.loads(response.read())

        self.assertEqual(body["status"], "ready")
        self.assertEqual(len(body["reactionRules"]), 12)
        self.assertGreaterEqual(len(body["reagentCatalogue"]), 10)
        self.assertEqual(body["limits"]["maxDepth"], 20)
        self.assertEqual(response.headers.get("Content-Type").split(";")[0], "application/json")
        self.assertEqual(body["requestId"], response.headers["X-Request-ID"])

    def test_post_returns_route_and_invalid_input_status(self):
        request = Request(
            self.base_url,
            data=json.dumps(
                {
                    "startingMaterials": [
                        {"id": "acetyl-chloride", "smiles": "CC(=O)Cl"}
                    ],
                    "targetProducts": [{"id": "acetamide", "smiles": "CC(N)=O"}],
                    "reagents": {"ammonia": 2},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            body = json.loads(response.read())
        self.assertEqual(body["status"], "route-found")
        self.assertIn("<svg", body["route"][0]["products"][0]["depictionSvg"])
        self.assertEqual(body["requestId"], response.headers["X-Request-ID"])

        invalid_request = Request(
            self.base_url,
            data=json.dumps({"startingMaterials": [], "targetProducts": []}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as error:
            urlopen(invalid_request, timeout=5)
        self.assertEqual(error.exception.code, 422)
        error_body = json.loads(error.exception.read())
        self.assertEqual(error_body["error"]["code"], "invalid_request")
        self.assertEqual(error_body["error"]["kind"], "user-input")
        self.assertTrue(error_body["requestId"])

    def test_unsupported_chemistry_is_not_returned_as_success(self):
        request = Request(
            self.base_url,
            data=json.dumps(
                {
                    "startingMaterials": [
                        {"id": "acid", "smiles": "CC(F)C(=O)Cl"}
                    ],
                    "targetProducts": [{"id": "amide", "smiles": "CC(F)C(N)=O"}],
                    "reagents": {"ammonia": 2},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as error:
            urlopen(request, timeout=5)
        self.assertEqual(error.exception.code, 422)
        self.assertEqual(
            json.loads(error.exception.read())["error"]["code"],
            "unsupported_chemistry",
        )

    def test_search_limit_is_a_structured_non_success_response(self):
        request = Request(
            self.base_url,
            data=json.dumps(
                {
                    "startingMaterials": [{"id": "acid", "smiles": "CC(=O)Cl"}],
                    "targetProducts": [{"id": "amide", "smiles": "CC(N)=O"}],
                    "reagents": {"ammonia": 2},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with patch("chemistry.reaction_planner.MAX_SEARCH_STATES", 0):
            with self.assertRaises(HTTPError) as error:
                urlopen(request, timeout=5)
        self.assertEqual(error.exception.code, 422)
        self.assertEqual(
            json.loads(error.exception.read())["error"]["code"],
            "search_limit_reached",
        )


class ReactionPlannerColdStartTests(unittest.TestCase):
    def test_planner_imports_with_installed_rdkit_dependency(self):
        source = """
from rdkit import Chem
import chemistry.reaction_planner
assert Chem.MolFromSmiles("CCO") is not None
assert hasattr(chemistry.reaction_planner, "handler")
"""
        repository_root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "-c", source],
            cwd=repository_root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
