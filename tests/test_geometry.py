import json
import math
import tarfile
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from rdkit import Chem
from rdkit.Chem import rdMolTransforms

from api.geometry import (
    GeometryInputError,
    _opsin_java_executable,
    generate_geometry,
    handler,
)


VALIDATION_MOLECULES = {
    "methane": "C",
    "ethane": "CC",
    "ethene": "C=C",
    "ethyne": "C#C",
    "ammonia": "N",
    "water": "O",
    "formaldehyde": "C=O",
    "carbon dioxide": "O=C=O",
    "benzene": "c1ccccc1",
    "toluene": "Cc1ccccc1",
    "ethanol": "CCO",
    "ethylamine": "CCN",
    "acetamide": "CC(=O)N",
    "acetic acid": "CC(=O)O",
    "ethyl acetate": "CCOC(=O)C",
    "acetate": "CC(=O)[O-]",
    "nitrobenzene": "[O-][N+](=O)c1ccccc1",
    "butadiene": "C=CC=C",
    "halogenated carbon": "CC(F)(Cl)Br",
    "branched alkane": "CC(C)(C)C",
    "cyclopropane": "C1CC1",
    "cyclobutane": "C1CCC1",
    "cyclopentane": "C1CCCC1",
    "cyclohexane": "C1CCCCC1",
    "naphthalene": "c1ccc2ccccc2c1",
    "norbornane": "C1CC2CCC1C2",
    "fused decalin": "C1CCC2CCCCC2C1",
    "macrocyclic alkane": "C1CCCCCCCCCCC1",
    "chiral alanine": "C[C@@H](N)C(=O)O",
    "glycylglycine": "NCC(=O)NCC(=O)O",
    "long-chain alkane": "CCCCCCCCCCCC",
}


def angle_degrees(center, first, second):
    a = [first[axis] - center[axis] for axis in ("x", "y", "z")]
    b = [second[axis] - center[axis] for axis in ("x", "y", "z")]
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    cosine = max(-1.0, min(1.0, dot / (norm_a * norm_b)))
    return math.degrees(math.acos(cosine))


def get_angle(result, center_index, first_index, second_index):
    positions = [atom["position"] for atom in result["atoms"]]
    return angle_degrees(
        positions[center_index], positions[first_index], positions[second_index]
    )


class GeometryGenerationTests(unittest.TestCase):
    def test_geometry_metadata_reports_molecular_weight_charge_and_stereochemistry(self):
        result = generate_geometry({"smiles": "C[C@H](O)C(=O)[O-]", "conformers": 2})

        self.assertAlmostEqual(result["metadata"]["molecularWeight"], 89.07, places=1)
        self.assertEqual(result["metadata"]["formalCharge"], -1)
        self.assertEqual(
            result["metadata"]["stereochemistry"],
            [{"atomIndex": 1, "label": "S"}],
        )
        self.assertEqual(result["metadata"]["bondStereochemistry"], [])

    def test_editor_graph_preserves_drawn_atoms_and_adds_implicit_hydrogens(self):
        result = generate_geometry(
            {
                "graph": {
                    "atoms": [
                        {"element": "C"},
                        {"element": "C"},
                        {"element": "O"},
                    ],
                    "bonds": [
                        {"from": 0, "to": 1, "order": 1},
                        {"from": 1, "to": 2, "order": 1},
                    ],
                },
                "conformers": 2,
            }
        )

        self.assertEqual(
            [atom["element"] for atom in result["atoms"][:3]], ["C", "C", "O"]
        )
        self.assertEqual(result["metadata"]["formula"], "C2H6O")
        self.assertEqual(
            sum(atom["element"] == "H" for atom in result["atoms"]), 6
        )
        self.assertEqual(
            {
                (bond["from"], bond["to"], bond["order"])
                for bond in result["bonds"]
                if bond["from"] < 3 and bond["to"] < 3
            },
            {(0, 1, 1.0), (1, 2, 1.0)},
        )

    def test_deployment_pins_the_python_312_chemistry_runtime(self):
        project_root = Path(__file__).resolve().parents[1]
        self.assertEqual(
            (project_root / ".python-version").read_text(encoding="utf-8").strip(),
            "3.12",
        )
        requirements = set(
            (project_root / "requirements.txt").read_text(encoding="utf-8").splitlines()
        )
        self.assertTrue(
            {
                "numpy==2.5.4",
                "rdkit==2026.3.5",
                "orthonym==1.1.0",
                "lxml==6.1.3",
                "JPype1==1.7.1",
                "packaging==26.3",
            }.issubset(requirements)
        )

    def test_bundled_runtime_archive_is_extracted_to_temporary_storage(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            vendor_directory = root / "vendor"
            vendor_directory.mkdir()
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            java_executable = root / "source" / "runtime" / "bin" / "java"
            java_executable.parent.mkdir(parents=True)
            java_executable.write_bytes(b"runtime executable")
            runtime_archive = vendor_directory / "runtime-linux-x64.tar.gz"
            with tarfile.open(runtime_archive, "w:gz") as archive:
                archive.add(java_executable.parents[1], arcname="runtime")

            with patch(
                "api.geometry.tempfile.gettempdir",
                return_value=str(temporary_root),
            ):
                extracted_java = _opsin_java_executable(vendor_directory)
                self.assertIsNotNone(extracted_java)
                self.assertEqual(
                    Path(extracted_java).read_bytes(), b"runtime executable"
                )
                self.assertEqual(
                    _opsin_java_executable(vendor_directory), extracted_java
                )

    def test_representative_structures_have_finite_3d_geometry(self):
        for name, smiles in VALIDATION_MOLECULES.items():
            with self.subTest(molecule=name):
                result = generate_geometry({"smiles": smiles, "conformers": 2})
                self.assertGreater(len(result["atoms"]), 0)
                self.assertGreater(len(result["bonds"]), 0)
                self.assertIn("<svg", result["depictionSvg"])
                self.assertIn("</svg>", result["depictionSvg"])
                self.assertIn(result["metadata"]["forceField"], ("MMFF94s", "UFF"))
                for atom in result["atoms"]:
                    self.assertTrue(
                        all(math.isfinite(value) for value in atom["position"].values())
                    )
                for bond in result["bonds"]:
                    self.assertGreater(
                        math.dist(
                            list(result["atoms"][bond["from"]]["position"].values()),
                            list(result["atoms"][bond["to"]]["position"].values()),
                        ),
                        0.1,
                    )

    def test_2d_depiction_is_generated_from_structure_without_mutating_identity(self):
        smiles = "C[C@H](O)C(=O)[O-]"
        molecule = Chem.MolFromSmiles(smiles)
        original_smiles = Chem.MolToSmiles(molecule, isomericSmiles=True)

        result = generate_geometry({"smiles": smiles, "conformers": 2})

        self.assertEqual(Chem.MolToSmiles(molecule, isomericSmiles=True), original_smiles)
        self.assertEqual(result["metadata"]["canonicalSmiles"], original_smiles)
        self.assertGreater(result["depictionSvg"].count("<path"), 10)
        self.assertIn("atom-2", result["depictionSvg"])

    def test_small_molecule_angles_agree_with_gas_phase_reference_ranges(self):
        cases = (
            ("water", "O", 0, 1, 2, 104.5, 1.0),
            ("ammonia", "N", 0, 1, 2, 106.7, 1.0),
            ("methane", "C", 0, 1, 2, 109.47, 0.1),
            ("carbon dioxide", "O=C=O", 1, 0, 2, 180.0, 0.1),
            ("ethyne", "C#C", 0, 1, 2, 180.0, 0.1),
            ("benzene", "c1ccccc1", 0, 1, 5, 120.0, 1.0),
            ("cyclopropane", "C1CC1", 0, 1, 2, 60.0, 1.0),
            ("cyclobutane", "C1CCC1", 1, 0, 2, 88.4, 3.0),
            ("cyclopentane", "C1CCCC1", 0, 1, 4, 105.0, 3.0),
            ("cyclohexane", "C1CCCCC1", 0, 1, 5, 111.5, 2.0),
            ("n-butane", "CCCC", 1, 0, 2, 112.2, 2.0),
            ("ethene", "C=C", 0, 1, 2, 121.7, 2.0),
            ("formaldehyde", "C=O", 0, 2, 3, 116.5, 2.0),
        )
        for name, smiles, center, first, second, reference, tolerance in cases:
            with self.subTest(molecule=name):
                result = generate_geometry({"smiles": smiles, "conformers": 2})
                angle = get_angle(result, center, first, second)
                self.assertAlmostEqual(angle, reference, delta=tolerance)

    def test_ring_puckering_and_hypervalent_geometry(self):
        cyclohexane = generate_geometry({"smiles": "C1CCCCC1", "conformers": 8})
        molecule = Chem.AddHs(Chem.MolFromSmiles("C1CCCCC1"))
        conformer = Chem.Conformer(len(cyclohexane["atoms"]))
        for index, atom in enumerate(cyclohexane["atoms"]):
            position = atom["position"]
            conformer.SetAtomPosition(
                index, (position["x"], position["y"], position["z"])
            )
        molecule.AddConformer(conformer, assignId=True)
        ring_torsions = [
            abs(
                rdMolTransforms.GetDihedralDeg(
                    molecule.GetConformer(),
                    index,
                    (index + 1) % 6,
                    (index + 2) % 6,
                    (index + 3) % 6,
                )
            )
            for index in range(6)
        ]
        self.assertTrue(all(45.0 <= torsion <= 65.0 for torsion in ring_torsions))

        phosphorus_pentafluoride = generate_geometry(
            {"smiles": "FP(F)(F)(F)F", "conformers": 4}
        )
        self.assertEqual(phosphorus_pentafluoride["metadata"]["forceField"], "UFF")
        center = 1
        axial_equatorial = get_angle(
            phosphorus_pentafluoride, center, 0, 3
        )
        equatorial = get_angle(phosphorus_pentafluoride, center, 3, 4)
        self.assertAlmostEqual(axial_equatorial, 90.0, delta=2.0)
        self.assertAlmostEqual(equatorial, 120.0, delta=2.0)

    def test_stereochemistry_is_preserved(self):
        result = generate_geometry(
            {"smiles": "C[C@@H](N)C(=O)O", "conformers": 2}
        )
        stereocenters = [
            atom["stereochemistry"]
            for atom in result["atoms"]
            if atom["stereochemistry"] is not None
        ]
        self.assertEqual(stereocenters, ["R"])

    def test_iupac_names_are_resolved_locally_and_keep_stereochemistry(self):
        cases = (
            ("2-methylpropan-1-ol", "C4H10O", None),
            ("2-hydroxybenzoic acid", "C7H6O3", None),
            ("N-(4-hydroxyphenyl)acetamide", "C8H9NO2", None),
            ("(2R)-butan-2-ol", "C4H10O", "R"),
        )
        for name, formula, expected_stereochemistry in cases:
            with self.subTest(name=name):
                result = generate_geometry(
                    {"iupacName": name, "conformers": 2}
                )
                self.assertEqual(result["metadata"]["inputFormat"], "iupacName")
                self.assertEqual(
                    result["metadata"]["nameResolutionEngine"], "OPSIN 2.9.0 (local)"
                )
                self.assertEqual(result["metadata"]["formula"], formula)
                self.assertEqual(
                    [
                        atom["stereochemistry"]
                        for atom in result["atoms"]
                        if atom["stereochemistry"] is not None
                    ],
                    [expected_stereochemistry] if expected_stereochemistry else [],
                )

    def test_unrecognized_iupac_names_fail_explicitly(self):
        with self.assertRaisesRegex(GeometryInputError, "OPSIN could not interpret"):
            generate_geometry({"iupacName": "not a chemical name"})
        with self.assertRaisesRegex(GeometryInputError, "exactly one"):
            generate_geometry({"iupacName": "ethanol", "smiles": "CCO"})

    def test_molfile_input_remains_supported(self):
        molblock = Chem.MolToMolBlock(Chem.MolFromSmiles("CCO"))
        result = generate_geometry({"molblock": molblock, "conformers": 2})
        self.assertEqual(result["metadata"]["inputFormat"], "molblock")
        self.assertEqual(result["metadata"]["formula"], "C2H6O")

    def test_aromatic_graph_and_formal_charges_are_supported(self):
        result = generate_geometry(
            {
                "graph": {
                    "atoms": [
                        {"element": "C", "aromatic": True},
                        {"element": "C", "aromatic": True},
                        {"element": "C", "aromatic": True},
                        {"element": "C", "aromatic": True},
                        {"element": "C", "aromatic": True},
                        {"element": "C", "aromatic": True},
                        {"element": "N", "formalCharge": 1},
                        {"element": "O"},
                        {"element": "O", "formalCharge": -1},
                    ],
                    "bonds": [
                        {"from": index, "to": (index + 1) % 6, "order": 1.5}
                        for index in range(6)
                    ]
                    + [
                        {"from": 0, "to": 6, "order": 1},
                        {"from": 6, "to": 7, "order": 2},
                        {"from": 6, "to": 8, "order": 1},
                    ],
                },
                "conformers": 2,
            }
        )
        self.assertEqual(result["metadata"]["formula"], "C6H5NO2")
        self.assertEqual(result["atoms"][6]["formalCharge"], 1)
        self.assertEqual(result["atoms"][8]["formalCharge"], -1)
        self.assertTrue(
            all(
                bond["aromatic"]
                for bond in result["bonds"]
                if bond["from"] < 6 and bond["to"] < 6
            )
        )

    def test_alkene_stereochemistry_and_unspecified_stereocentres(self):
        trans_2_butene = generate_geometry(
            {"smiles": "C/C=C/C", "conformers": 2}
        )
        stereo_bonds = [
            bond["stereochemistry"]
            for bond in trans_2_butene["bonds"]
            if bond["stereochemistry"] != "STEREONONE"
        ]
        self.assertIn("STEREOE", stereo_bonds)

        unspecified = generate_geometry(
            {"smiles": "CC(F)(Cl)Br", "conformers": 2}
        )
        self.assertTrue(
            any("unspecified stereocentres" in warning for warning in unspecified["metadata"]["warnings"])
        )
        self.assertEqual(unspecified["metadata"]["canonicalSmiles"], "CC(F)(Cl)Br")
        self.assertEqual(unspecified["metadata"]["stereochemistry"], [])
        self.assertEqual(unspecified["metadata"]["unspecifiedStereocentres"], [1])
        self.assertTrue(
            all(atom["stereochemistry"] is None for atom in unspecified["atoms"])
        )

        unspecified_alkene = generate_geometry({"smiles": "CC=CC", "conformers": 2})
        self.assertEqual(unspecified_alkene["metadata"]["canonicalSmiles"], "CC=CC")
        self.assertEqual(unspecified_alkene["metadata"]["bondStereochemistry"], [])
        self.assertTrue(
            all(
                bond["stereochemistry"] == "STEREONONE"
                for bond in unspecified_alkene["bonds"]
            )
        )

    def test_radical_and_charged_graphs_preserve_formula_and_electron_state(self):
        nitrogen_dioxide = generate_geometry(
            {
                "graph": {
                    "atoms": [
                        {"element": "N"},
                        {"element": "O"},
                        {"element": "O", "radicalElectrons": 1},
                    ],
                    "bonds": [
                        {"from": 0, "to": 1, "order": 2},
                        {"from": 0, "to": 2, "order": 1},
                    ],
                },
                "conformers": 2,
            }
        )
        self.assertEqual(nitrogen_dioxide["metadata"]["formula"], "NO2")
        self.assertEqual(
            sum(atom["radicalElectrons"] for atom in nitrogen_dioxide["atoms"]), 1
        )
        self.assertTrue(
            any("unpaired electron" in warning for warning in nitrogen_dioxide["metadata"]["warnings"])
        )

        dinitrogen_tetroxide = generate_geometry(
            {
                "graph": {
                    "atoms": [
                        {"element": "N", "formalCharge": 1},
                        {"element": "N", "formalCharge": 1},
                        {"element": "O"},
                        {"element": "O", "formalCharge": -1},
                        {"element": "O", "formalCharge": -1},
                        {"element": "O"},
                    ],
                    "bonds": [
                        {"from": 0, "to": 1, "order": 1},
                        {"from": 0, "to": 2, "order": 2},
                        {"from": 0, "to": 3, "order": 1},
                        {"from": 1, "to": 4, "order": 1},
                        {"from": 1, "to": 5, "order": 2},
                    ],
                },
                "conformers": 2,
            }
        )
        self.assertEqual(dinitrogen_tetroxide["metadata"]["formula"], "N2O4")
        self.assertEqual(
            [atom["formalCharge"] for atom in dinitrogen_tetroxide["atoms"][:6]],
            [1, 1, 0, -1, -1, 0],
        )

    def test_molecular_hydrogen_is_supported_as_a_bonded_diatomic(self):
        result = generate_geometry({"smiles": "[H][H]", "conformers": 2})
        self.assertEqual(result["metadata"]["formula"], "H2")
        self.assertEqual(len(result["atoms"]), 2)
        self.assertEqual(len(result["bonds"]), 1)

    def test_spin_multiplicity_is_validated_and_reported_as_unmodeled(self):
        oxygen = generate_geometry(
            {
                "graph": {
                    "atoms": [{"element": "O"}, {"element": "O"}],
                    "bonds": [{"from": 0, "to": 1, "order": 2}],
                },
                "spinMultiplicity": 3,
                "conformers": 2,
            }
        )
        self.assertEqual(oxygen["metadata"]["spinMultiplicity"], 3)
        self.assertTrue(
            any("not used to parameterize" in warning for warning in oxygen["metadata"]["warnings"])
        )
        with self.assertRaises(GeometryInputError):
            generate_geometry(
                {
                    "graph": {
                        "atoms": [{"element": "O"}, {"element": "O"}],
                        "bonds": [{"from": 0, "to": 1, "order": 2}],
                    },
                    "spinMultiplicity": 2,
                }
            )

    def test_butane_torsion_is_a_staggered_low_energy_conformer(self):
        result = generate_geometry({"smiles": "CCCC"})
        molecule = Chem.AddHs(Chem.MolFromSmiles("CCCC"))
        conformer = Chem.Conformer(len(result["atoms"]))
        for index, atom in enumerate(result["atoms"]):
            position = atom["position"]
            conformer.SetAtomPosition(
                index, (position["x"], position["y"], position["z"])
            )
        molecule.AddConformer(conformer, assignId=True)
        torsion = abs(
            rdMolTransforms.GetDihedralDeg(molecule.GetConformer(), 0, 1, 2, 3)
        )
        self.assertGreaterEqual(torsion, 150.0)
        self.assertLessEqual(torsion, 180.0)

    def test_invalid_or_unparameterized_input_fails_explicitly(self):
        for payload in (
            {"smiles": "C1"},
            {"smiles": "C", "molblock": "invalid"},
            {"graph": {"atoms": [], "bonds": []}},
            {"iupacName": "x" * 501},
            {"smiles": "C" * 151},
            {"smiles": "FS(F)(F)(F)(F)F"},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(GeometryInputError):
                    generate_geometry(payload)


class GeometryEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.endpoint = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_health_check_and_geometry_response(self):
        with urlopen(f"{self.endpoint}/api/geometry", timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(json.load(response)["status"], "ready")

        request = Request(
            f"{self.endpoint}/api/geometry",
            data=b'{"smiles":"O","conformers":2}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            result = json.load(response)
        self.assertEqual(result["metadata"]["formula"], "H2O")
        self.assertEqual(len(result["atoms"]), 3)

        name_request = Request(
            f"{self.endpoint}/api/geometry",
            data=b'{"iupacName":"2-methylpropan-1-ol","conformers":2}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(name_request, timeout=20) as response:
            name_result = json.load(response)
        self.assertEqual(name_result["metadata"]["formula"], "C4H10O")
        self.assertEqual(name_result["metadata"]["inputFormat"], "iupacName")

    def test_planner_rewrite_dispatches_through_shared_chemistry_function(self):
        with urlopen(
            f"{self.endpoint}/api/geometry?service=reaction_planner", timeout=5
        ) as response:
            health = json.load(response)
        self.assertEqual(health["status"], "ready")

        request = Request(
            f"{self.endpoint}/api/geometry?service=reaction_planner",
            data=json.dumps(
                {
                    "startingMaterials": [
                        {
                            "id": "acid-chloride",
                            "smiles": "CC(=O)Cl",
                            "quantity": 1,
                        }
                    ],
                    "targetProducts": [
                        {"id": "acetamide", "smiles": "CC(N)=O", "quantity": 1}
                    ],
                    "reagents": {"ammonia": 2},
                    "reagentMode": "manual",
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=20) as response:
            result = json.load(response)
        self.assertEqual(result["status"], "route-found")
        self.assertEqual(
            result["route"][0]["products"][0]["canonicalSmiles"], "CC(N)=O"
        )

        unsupported_request = Request(
            f"{self.endpoint}/api/geometry?service=reaction_planner",
            data=json.dumps(
                {
                    "startingMaterials": [{"smiles": "CCO", "quantity": 1}],
                    "targetProducts": [{"smiles": "CC(N)=O", "quantity": 1}],
                    "reagentMode": "manual",
                    "reagents": {},
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as error:
            urlopen(unsupported_request, timeout=10)
        self.assertEqual(error.exception.code, 422)
        self.assertIn(
            "diagnostics", json.loads(error.exception.read())["error"]
        )

    def test_invalid_requests_return_client_errors(self):
        for body, expected_status in (
            (b"{", 400),
            (b'{"smiles":"C1"}', 422),
            (b'{"iupacName":"not a chemical name"}', 422),
        ):
            request = Request(
                f"{self.endpoint}/api/geometry",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.subTest(expected_status=expected_status):
                with self.assertRaises(HTTPError) as error:
                    urlopen(request, timeout=5)
                self.assertEqual(error.exception.code, expected_status)

    def test_missing_local_java_runtime_returns_service_unavailable(self):
        request = Request(
            f"{self.endpoint}/api/geometry",
            data=b'{"iupacName":"ethanol"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with patch("api.geometry.shutil.which", return_value=None):
            with self.assertRaises(HTTPError) as error:
                urlopen(request, timeout=5)
        self.assertEqual(error.exception.code, 503)


if __name__ == "__main__":
    unittest.main()
