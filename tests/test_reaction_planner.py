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
from rdkit import Chem


class ReactionPlanningTests(unittest.TestCase):
    def test_auto_mode_supports_priority_named_synthesis_challenges(self):
        challenges = [
            ("ethanol", "CCO", "ethanoic acid", "CC(=O)O", "primary-alcohol-to-carboxylic-acid"),
            ("propan-2-ol", "CC(O)C", "propanone", "CC(=O)C", "secondary-alcohol-to-ketone"),
            ("benzene", "c1ccccc1", "nitrobenzene", "O=[N+]([O-])c1ccccc1", "benzene-nitration"),
            ("2-hydroxybenzoic acid", "O=C(O)c1ccccc1O", "2-acetyloxybenzoic acid", "CC(=O)Oc1ccccc1C(=O)O", "phenolic-o-acetylation"),
            ("4-aminophenol", "Nc1ccc(O)cc1", "N-(4-hydroxyphenyl)acetamide", "CC(=O)Nc1ccc(O)cc1", "aniline-n-acetylation"),
            ("benzene", "c1ccccc1", "1-phenylethan-1-one", "CC(=O)c1ccccc1", "benzene-friedel-crafts-acylation"),
            ("benzene", "c1ccccc1", "ethylbenzene", "CCc1ccccc1", "benzene-friedel-crafts-ethylation"),
            ("benzaldehyde", "O=Cc1ccccc1", "phenylmethanol", "OCc1ccccc1", "aldehyde-hydrogenation"),
        ]
        for start_name, start_smiles, target_name, target_smiles, expected_rule in challenges:
            with self.subTest(target=target_name):
                result = plan_synthesis(
                    {
                        "startingMaterials": [
                            {"id": "feedstock", "name": start_name, "smiles": start_smiles}
                        ],
                        "targetProducts": [
                            {"id": "target", "name": target_name, "smiles": target_smiles}
                        ],
                        "reagentMode": "auto",
                    }
                )
                self.assertEqual(result["status"], "route-found")
                self.assertEqual([step["reactionId"] for step in result["route"]], [expected_rule])
                self.assertEqual(
                    result["route"][-1]["products"][
                        next(
                            index
                            for index, product in enumerate(result["route"][-1]["products"])
                            if product["role"] == "desired product"
                        )
                    ]["canonicalSmiles"],
                    Chem.MolToSmiles(Chem.MolFromSmiles(target_smiles), canonical=True, isomericSmiles=True),
                )

    def test_kolbe_schmitt_uses_phenol_and_carbon_dioxide_with_workup(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "phenol", "name": "phenol", "smiles": "Oc1ccccc1"},
                    {"id": "carbon-dioxide", "name": "carbon dioxide", "smiles": "O=C=O"},
                ],
                "targetProducts": [
                    {"id": "salicylic-acid", "name": "2-hydroxybenzoic acid", "smiles": "O=C(O)c1ccccc1O"}
                ],
                "reagentMode": "auto",
            }
        )

        self.assertEqual(
            [step["reactionId"] for step in result["route"]],
            ["phenol-deprotonation", "kolbe-schmitt-carboxylation", "carboxylate-acidification"],
        )
        acidification = result["route"][-1]
        salicylic_acid = next(
            product for product in acidification["products"] if product["role"] == "desired product"
        )
        carbon_sources = {
            atom["origin"]["sourceId"]
            for atom in salicylic_acid["atoms"]
            if atom["element"] == "C"
        }
        self.assertEqual(carbon_sources, {"phenol", "carbon-dioxide"})
        for step in result["route"]:
            self.assertTrue(step["validation"]["atomBalanceChecked"])
            self.assertTrue(step["validation"]["chargeBalanceChecked"])

    def test_strecker_route_is_racemic_unspecified_and_tracks_three_feedstocks(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "ethanal", "name": "ethanal", "smiles": "CC=O"},
                    {"id": "hydrogen-cyanide", "name": "hydrogen cyanide", "smiles": "C#N"},
                    {"id": "ammonia", "name": "ammonia", "smiles": "N"},
                ],
                "targetProducts": [
                    {"id": "alanine", "name": "2-aminopropanoic acid", "smiles": "CC(N)C(=O)O"}
                ],
                "reagentMode": "auto",
            }
        )

        self.assertEqual(
            [step["reactionId"] for step in result["route"]],
            [
                "strecker-imine-formation",
                "strecker-cyanide-addition",
                "aminonitrile-hydrolysis",
                "carboxylate-acidification",
            ],
        )
        alanine = next(
            product
            for product in result["route"][-1]["products"]
            if product["role"] == "desired product"
        )
        self.assertEqual(alanine["unspecifiedStereocentres"], [1])
        origins = {
            atom["origin"]["sourceId"]
            for atom in alanine["atoms"]
            if atom["element"] in {"C", "N"}
        }
        self.assertEqual(
            origins,
            {
                "ethanal",
                "hydrogen-cyanide",
                "ammonia",
            },
        )
        self.assertTrue(
            any(
                atom["origin"]["sourceType"] == "reagent"
                for atom in alanine["atoms"]
                if atom["element"] == "O"
            )
        )
        for step in result["route"]:
            self.assertTrue(step["validation"]["atomBalanceChecked"])
            self.assertTrue(step["validation"]["chargeBalanceChecked"])

    def test_strecker_route_does_not_claim_enantiopure_s_alanine(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "ethanal", "smiles": "CC=O"},
                    {"id": "hydrogen-cyanide", "smiles": "C#N"},
                    {"id": "ammonia", "smiles": "N"},
                ],
                "targetProducts": [
                    {"id": "l-alanine", "smiles": "C[C@@H](N)C(=O)O"}
                ],
                "reagentMode": "auto",
            }
        )
        self.assertEqual(result["status"], "no-supported-route")

    def test_paal_knorr_heterocycle_route_tracks_dialdehyde_and_ammonia_atoms(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "butane-1,4-dial", "name": "butane-1,4-dial", "smiles": "O=CCCC=O"},
                    {"id": "ammonia", "name": "ammonia", "smiles": "N"},
                ],
                "targetProducts": [
                    {"id": "pyrrole", "name": "1H-pyrrole", "smiles": "c1cc[nH]c1"}
                ],
                "reagentMode": "auto",
            }
        )

        self.assertEqual(result["status"], "route-found")
        self.assertEqual([step["reactionId"] for step in result["route"]], ["paal-knorr-pyrrole-synthesis"])
        step = result["route"][0]
        pyrrole = next(product for product in step["products"] if product["role"] == "desired product")
        self.assertEqual(pyrrole["canonicalSmiles"], "c1cc[nH]c1")
        self.assertEqual(
            {
                (atom["element"], atom["origin"]["sourceId"])
                for atom in pyrrole["atoms"]
                if atom["element"] in {"C", "N"}
            },
            {
                ("C", "butane-1,4-dial"),
                ("N", "ammonia"),
            },
        )
        self.assertEqual(
            sum(product["formula"] == "H2O" for product in step["products"]),
            2,
        )
        self.assertTrue(step["validation"]["atomBalanceChecked"])
        self.assertTrue(step["validation"]["chargeBalanceChecked"])

    def test_substituted_aromatic_nitration_is_rejected_without_regioselectivity_model(self):
        result = plan_synthesis(
            {
                "startingMaterials": [{"id": "toluene", "smiles": "Cc1ccccc1"}],
                "targetProducts": [{"id": "nitrotoluene", "smiles": "Cc1ccccc1[N+](=O)[O-]"}],
                "reagentMode": "auto",
            }
        )
        self.assertEqual(result["status"], "no-supported-route")

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

    def test_auto_mode_prefers_balanced_fischer_esterification(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "ethanoic-acid", "smiles": "CC(=O)O"},
                    {"id": "ethanol", "smiles": "CCO"},
                ],
                "targetProducts": [{"id": "ethyl-ethanoate", "smiles": "CCOC(C)=O"}],
                "reagentMode": "auto",
            }
        )

        self.assertEqual(result["status"], "route-found")
        self.assertEqual(
            [step["reactionId"] for step in result["route"]],
            ["fischer-esterification"],
        )
        step = result["route"][0]
        products = {product["canonicalSmiles"]: product for product in step["products"]}
        self.assertEqual(products["CCOC(C)=O"]["role"], "desired product")
        self.assertEqual(products["O"]["formula"], "H2O")
        self.assertEqual(
            {item["id"] for item in step["conditionsUsed"]}, {"sulfuric-acid"}
        )
        self.assertTrue(step["validation"]["atomBalanceChecked"])
        self.assertTrue(step["validation"]["chargeBalanceChecked"])
        self.assertEqual(
            {
                atom["origin"]["sourceId"]
                for atom in products["CCOC(C)=O"]["atoms"]
                if atom["element"] == "C"
            },
            {"ethanoic-acid", "ethanol"},
        )

    def test_fischer_esterification_rejects_phenolic_oxygen_as_an_alcohol_site(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "ethanoic-acid", "smiles": "CC(=O)O"},
                    {"id": "phenol", "smiles": "Oc1ccccc1"},
                ],
                "targetProducts": [
                    {"id": "phenyl-ethanoate", "smiles": "CC(=O)Oc1ccccc1"}
                ],
                "reagentMode": "auto",
            }
        )

        self.assertEqual(result["status"], "no-supported-route")

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
                "fischer-esterification",
                [("acid", "CC(=O)O", 1), ("alcohol", "CCO", 1)],
                "CCOC(C)=O",
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
            ("primary-alcohol-to-aldehyde", [("ethanol", "CCO", 1)], "CC=O", 1),
            ("primary-alcohol-to-carboxylic-acid", [("ethanol", "CCO", 1)], "CC(=O)O", 1),
            ("secondary-alcohol-to-ketone", [("isopropanol", "CC(O)C", 1)], "CC(=O)C", 1),
            ("aldehyde-to-carboxylic-acid", [("ethanal", "CC=O", 1)], "CC(=O)O", 1),
            ("aldehyde-hydrogenation", [("benzaldehyde", "O=Cc1ccccc1", 1)], "OCc1ccccc1", 1),
            ("benzene-nitration", [("benzene", "c1ccccc1", 1)], "O=[N+]([O-])c1ccccc1", 1),
            ("benzene-friedel-crafts-acylation", [("benzene", "c1ccccc1", 1)], "CC(=O)c1ccccc1", 1),
            ("benzene-friedel-crafts-ethylation", [("benzene", "c1ccccc1", 1)], "CCc1ccccc1", 1),
            ("phenolic-o-acetylation", [("salicylic-acid", "O=C(O)c1ccccc1O", 1)], "CC(=O)Oc1ccccc1C(=O)O", 1),
            ("aniline-n-acetylation", [("4-aminophenol", "Nc1ccc(O)cc1", 1)], "CC(=O)Nc1ccc(O)cc1", 1),
            ("phenol-deprotonation", [("phenol", "Oc1ccccc1", 1)], "[O-]c1ccccc1", 1),
            ("kolbe-schmitt-carboxylation", [("phenoxide", "[O-]c1ccccc1", 1), ("carbon-dioxide", "O=C=O", 1)], "O=C([O-])c1ccccc1O", 1),
            ("strecker-imine-formation", [("ethanal", "CC=O", 1), ("ammonia", "N", 1)], "CC=N", 1),
            ("strecker-cyanide-addition", [("imine", "CC=N", 1), ("hydrogen-cyanide", "C#N", 1)], "CC(N)C#N", 1),
            ("aminonitrile-hydrolysis", [("aminonitrile", "CC(N)C#N", 1)], "CC(N)C(=O)[O-]", 1),
            ("paal-knorr-pyrrole-synthesis", [("butane-1,4-dial", "O=CCCC=O", 1), ("ammonia", "N", 1)], "c1cc[nH]c1", 1),
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

    def test_multi_step_route_preserves_original_atom_sources(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {
                        "id": "ethyl-benzoate",
                        "name": "ethyl benzoate",
                        "smiles": "CCOC(=O)c1ccccc1",
                    }
                ],
                "targetProducts": [{"id": "benzamide", "smiles": "NC(=O)c1ccccc1"}],
                "reagentMode": "auto",
            }
        )

        self.assertEqual(
            [step["reactionId"] for step in result["route"]],
            [
                "ester-saponification",
                "carboxylate-acidification",
                "acid-chloride-formation",
                "acyl-chloride-ammonolysis",
            ],
        )
        for step in result["route"]:
            for product in step["products"]:
                for atom in product["atoms"]:
                    origin = atom["origin"]
                    if origin["sourceType"] == "startingMaterial":
                        self.assertEqual(origin["sourceId"], "ethyl-benzoate")
                    self.assertNotRegex(origin["sourceId"], r"^step-\d+-product-")

        benzamide = next(
            product
            for product in result["route"][-1]["products"]
            if product["role"] == "desired product"
        )
        self.assertEqual(
            {
                atom["origin"]["sourceId"]
                for atom in benzamide["atoms"]
                if atom["element"] == "N"
            },
            {"ammonia-step-4-equivalent-1"},
        )
        self.assertEqual(
            {
                atom["origin"]["sourceId"]
                for atom in benzamide["atoms"]
                if atom["element"] == "C"
            },
            {"ethyl-benzoate"},
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
        self.assertEqual(
            result["search"]["candidateReactions"],
            result["search"]["generatedStates"],
        )
        self.assertGreaterEqual(result["search"]["generatedStates"], 4)
        self.assertGreaterEqual(result["search"]["duplicateStates"], 0)
        self.assertGreaterEqual(result["search"]["maxQueueSize"], 1)
        self.assertEqual(result["search"]["maxDepthReached"], 4)
        self.assertGreaterEqual(result["search"]["elapsedMilliseconds"], 0)

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

    def test_inorganic_starting_materials_are_valid_but_nonorganic_targets_are_rejected(self):
        result = plan_synthesis(
            {
                "startingMaterials": [
                    {"id": "ethanal", "smiles": "CC=O"},
                    {"id": "hydrogen-cyanide", "smiles": "C#N"},
                    {"id": "ammonia", "smiles": "N"},
                ],
                "targetProducts": [
                    {"id": "l-alanine", "smiles": "C[C@H](N)C(=O)O"}
                ],
                "reagentMode": "auto",
            }
        )
        self.assertEqual(result["status"], "no-supported-route")

        invalid_cases = (
            {
                "startingMaterials": [
                    {"id": "acetyl-chloride", "smiles": "CC(=O)Cl"}
                ],
                "targetProducts": [{"id": "water", "smiles": "O"}],
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
        self.assertEqual(len(body["reactionRules"]), 29)
        self.assertGreaterEqual(len(body["reagentCatalogue"]), 10)
        self.assertEqual(body["limits"]["maxDepth"], 20)
        self.assertRegex(body["version"]["catalogue"], r"^[0-9a-f]{16}$")
        self.assertIn("commit", body["version"])
        self.assertIn("build", body["version"])
        if body["version"]["commit"] is not None:
            self.assertRegex(body["version"]["commit"], r"^[0-9a-fA-F]+$")
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
