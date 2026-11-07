import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from api.reaction_planner import PlannerInputError, plan_synthesis
from api.reaction_planner import handler as reaction_handler


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
        self.assertEqual(step["reactionId"], "acetyl-chloride-ammonolysis")
        self.assertIn("Ammonia substitutes", step["shortDescription"])
        products = {product["formula"]: product for product in step["products"]}
        self.assertEqual(products["C2H5NO"]["canonicalSmiles"], "CC(N)=O")
        self.assertIn("Cl-", products)
        self.assertIn("H4N+", products)
        self.assertTrue(step["validation"]["atomBalanceChecked"])
        self.assertTrue(step["validation"]["chargeBalanceChecked"])
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
            {"ammonia-equivalent-1", "ammonia-equivalent-2"},
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
            ["acetyl-chloride-ammonolysis", "acetyl-chloride-ethanolysis"],
        )
        self.assertEqual(result["search"]["objective"], "minimum number of curated reaction steps")

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
            [{"name": "ammonia", "formula": "NH3", "quantity": 2}],
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

    def test_non_exemplar_acid_chloride_is_not_generalized(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "propionyl-chloride", "smiles": "CCC(=O)Cl"}
                ],
                "targetProducts": [{"id": "propanamide", "smiles": "CCC(N)=O"}],
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
        self.assertEqual(len(body["reactionRules"]), 2)
        self.assertEqual(body["limits"]["maxDepth"], 20)

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

        invalid_request = Request(
            self.base_url,
            data=json.dumps({"startingMaterials": [], "targetProducts": []}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as error:
            urlopen(invalid_request, timeout=5)
        self.assertEqual(error.exception.code, 422)


if __name__ == "__main__":
    unittest.main()
