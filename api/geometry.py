import base64
import binascii
import json
import logging
import math
import os
import shutil
import subprocess
import tarfile
import tempfile
import threading
import uuid
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit


class GeometryInputError(ValueError):
    pass


class GeometryEngineUnavailableError(RuntimeError):
    pass


_OPSIN_RUNTIME_LOCK = threading.Lock()

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors

from api.molecule_depiction import render_2d_svg


_LOGGER = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 1_000_000
MAX_HEAVY_ATOMS = 150
DEFAULT_RANDOM_SEED = 0xC0FFEE


def _opsin_java_executable(vendor_directory: Path) -> str | None:
    bundled_java = vendor_directory / "runtime" / "bin" / "java"
    if bundled_java.is_file():
        return str(bundled_java)

    runtime_archive = vendor_directory / "runtime-linux-x64.tar.gz"
    if runtime_archive.is_file():
        runtime_root = Path(tempfile.gettempdir()) / "atomview-opsin-runtime"
        extracted_java = runtime_root / "runtime" / "bin" / "java"
        if not extracted_java.is_file():
            with _OPSIN_RUNTIME_LOCK:
                if not extracted_java.is_file():
                    staging_directory = Path(
                        tempfile.mkdtemp(prefix="atomview-opsin-runtime-")
                    )
                    try:
                        with tarfile.open(runtime_archive, "r:gz") as archive:
                            archive.extractall(staging_directory, filter="data")
                        staged_java = staging_directory / "runtime" / "bin" / "java"
                        if not staged_java.is_file():
                            raise GeometryEngineUnavailableError(
                                "The bundled IUPAC runtime archive is incomplete."
                            )
                        if runtime_root.exists():
                            shutil.rmtree(runtime_root)
                        runtime_root.mkdir(parents=True, exist_ok=True)
                        (staging_directory / "runtime").replace(runtime_root / "runtime")
                    except (OSError, tarfile.TarError, ValueError) as error:
                        raise GeometryEngineUnavailableError(
                            "The bundled IUPAC runtime could not be extracted."
                        ) from error
                    finally:
                        shutil.rmtree(staging_directory, ignore_errors=True)
        return str(extracted_java)

    return shutil.which("java")


def _molecule_from_iupac_name(name: Any) -> tuple[Chem.Mol, list[str]]:
    if not isinstance(name, str) or not name.strip() or len(name) > 500:
        raise GeometryInputError(
            "IUPAC name must be a non-empty string of at most 500 characters."
        )
    name = name.strip()
    if "\n" in name or "\r" in name:
        raise GeometryInputError("IUPAC name must be a single line.")

    vendor_directory = Path(__file__).parent / "vendor" / "opsin"
    jar_path = vendor_directory / "opsin-core-2.9.0.jar"
    bridge_directory = vendor_directory / "bridge"
    java_executable = _opsin_java_executable(vendor_directory)
    if java_executable is None or not jar_path.is_file() or not (
        bridge_directory / "OpsinBridge.class"
    ).is_file():
        raise GeometryEngineUnavailableError(
            "The local IUPAC parser is unavailable. Install Java 21 locally or rebuild the deployment."
        )

    class_path = os.pathsep.join((str(bridge_directory), str(jar_path)))
    try:
        process = subprocess.run(
            [
                java_executable,
                "-Xms16m",
                "-Xmx256m",
                "-cp",
                class_path,
                "OpsinBridge",
            ],
            input=f"{name}\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise GeometryInputError(
            "Parsing this IUPAC name took too long; please simplify or shorten it."
        ) from error
    except OSError as error:
        raise GeometryEngineUnavailableError(
            "The local IUPAC parser could not start its Java runtime."
        ) from error

    if process.returncode != 0:
        raise GeometryEngineUnavailableError(
            "The local IUPAC parser exited unexpectedly."
        )
    fields = process.stdout.rstrip("\r\n").split("\t")
    if len(fields) != 3:
        raise GeometryEngineUnavailableError(
            "The local IUPAC parser returned an invalid response."
        )
    try:
        status = fields[0]
        smiles = base64.b64decode(fields[1], validate=True).decode("utf-8")
        message = base64.b64decode(fields[2], validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        raise GeometryEngineUnavailableError(
            "The local IUPAC parser returned an invalid response."
        ) from error

    if status == "FAILURE" or not smiles:
        detail = f" ({message[:300]})" if message else ""
        raise GeometryInputError(f"OPSIN could not interpret this IUPAC name{detail}.")
    if status not in ("SUCCESS", "WARNING"):
        raise GeometryEngineUnavailableError(
            "The local IUPAC parser returned an unsupported status."
        )

    molecule = Chem.MolFromSmiles(smiles, sanitize=True)
    if molecule is None:
        raise GeometryInputError(
            "OPSIN interpreted this name, but RDKit could not parse the resulting structure."
        )
    warnings = (
        [f"OPSIN reported: {message or 'the name interpretation has a limitation.'}"]
        if status == "WARNING"
        else []
    )
    return molecule, warnings


def _molecule_from_graph(graph: dict[str, Any]) -> Chem.Mol:
    atoms = graph.get("atoms")
    bonds = graph.get("bonds")
    if not isinstance(atoms, list) or not atoms:
        raise GeometryInputError("A graph must contain at least one atom.")
    if not isinstance(bonds, list):
        raise GeometryInputError("Graph bonds must be an array.")

    editable = Chem.RWMol()
    aromatic_atom_indices: set[int] = set()
    for index, item in enumerate(atoms):
        if not isinstance(item, dict):
            raise GeometryInputError(f"Atom {index} must be an object.")
        element = item.get("element")
        if not isinstance(element, str):
            raise GeometryInputError(f"Atom {index} is missing an element symbol.")
        atomic_number = Chem.GetPeriodicTable().GetAtomicNumber(element)
        if atomic_number == 0:
            raise GeometryInputError(f"Unsupported element symbol at atom {index}: {element!r}.")

        atom = Chem.Atom(atomic_number)
        formal_charge = item.get("formalCharge", 0)
        if isinstance(formal_charge, bool) or not isinstance(formal_charge, int):
            raise GeometryInputError(f"Atom {index} formalCharge must be an integer.")
        atom.SetFormalCharge(formal_charge)

        radical_electrons = item.get("radicalElectrons", 0)
        if (
            isinstance(radical_electrons, bool)
            or not isinstance(radical_electrons, int)
            or not 0 <= radical_electrons <= 3
        ):
            raise GeometryInputError(f"Atom {index} radicalElectrons must be an integer from 0 to 3.")
        atom.SetNumRadicalElectrons(radical_electrons)

        isotope = item.get("isotope", 0)
        if isinstance(isotope, bool) or not isinstance(isotope, int) or isotope < 0:
            raise GeometryInputError(f"Atom {index} isotope must be a non-negative integer.")
        if isotope:
            atom.SetIsotope(isotope)

        explicit_hydrogens = item.get("explicitHydrogens")
        if explicit_hydrogens is not None:
            if (
                isinstance(explicit_hydrogens, bool)
                or not isinstance(explicit_hydrogens, int)
                or explicit_hydrogens < 0
                or explicit_hydrogens > 4
            ):
                raise GeometryInputError(
                    f"Atom {index} explicitHydrogens must be an integer from 0 to 4."
                )
            atom.SetNumExplicitHs(explicit_hydrogens)
            atom.SetNoImplicit(True)
        elif radical_electrons:
            atom.SetNoImplicit(True)

        aromatic = item.get("aromatic", False)
        if not isinstance(aromatic, bool):
            raise GeometryInputError(f"Atom {index} aromatic must be a boolean.")
        if aromatic:
            atom.SetIsAromatic(True)
            aromatic_atom_indices.add(index)

        chiral_tag = item.get("chiralTag")
        if chiral_tag is not None:
            chiral_tags = {
                "CHI_TETRAHEDRAL_CW": Chem.ChiralType.CHI_TETRAHEDRAL_CW,
                "CHI_TETRAHEDRAL_CCW": Chem.ChiralType.CHI_TETRAHEDRAL_CCW,
            }
            if chiral_tag not in chiral_tags:
                raise GeometryInputError(f"Unsupported chiralTag on atom {index}: {chiral_tag!r}.")
            atom.SetChiralTag(chiral_tags[chiral_tag])

        editable.AddAtom(atom)

    order_map = {
        1: Chem.BondType.SINGLE,
        1.5: Chem.BondType.AROMATIC,
        2: Chem.BondType.DOUBLE,
        3: Chem.BondType.TRIPLE,
    }
    seen_bonds: set[tuple[int, int]] = set()
    for index, item in enumerate(bonds):
        if not isinstance(item, dict):
            raise GeometryInputError(f"Bond {index} must be an object.")
        start = item.get("from")
        end = item.get("to")
        order = item.get("order", 1)
        if (
            isinstance(start, bool)
            or not isinstance(start, int)
            or isinstance(end, bool)
            or not isinstance(end, int)
            or start < 0
            or end < 0
            or start >= len(atoms)
            or end >= len(atoms)
            or start == end
        ):
            raise GeometryInputError(f"Bond {index} has invalid atom indices.")
        if isinstance(order, bool) or order not in order_map:
            raise GeometryInputError(
                f"Bond {index} order must be one of 1, 1.5, 2, or 3."
            )
        key = (min(start, end), max(start, end))
        if key in seen_bonds:
            raise GeometryInputError(f"Duplicate bond between atoms {key[0]} and {key[1]}.")
        seen_bonds.add(key)

        bond_type = order_map[order]
        editable.AddBond(start, end, bond_type)
        if bond_type == Chem.BondType.AROMATIC:
            aromatic_atom_indices.update((start, end))

        stereo = item.get("stereo")
        if stereo is not None:
            stereo_types = {
                "STEREOE": Chem.BondStereo.STEREOE,
                "STEREOZ": Chem.BondStereo.STEREOZ,
                "STEREOCIS": Chem.BondStereo.STEREOCIS,
                "STEREOTRANS": Chem.BondStereo.STEREOTRANS,
            }
            if stereo not in stereo_types:
                raise GeometryInputError(f"Unsupported stereo value on bond {index}: {stereo!r}.")
            stereo_atoms = item.get("stereoAtoms")
            if (
                not isinstance(stereo_atoms, list)
                or len(stereo_atoms) != 2
                or any(
                    isinstance(atom_index, bool)
                    or not isinstance(atom_index, int)
                    or atom_index < 0
                    or atom_index >= len(atoms)
                    for atom_index in stereo_atoms
                )
            ):
                raise GeometryInputError(
                    f"Bond {index} stereo requires two valid stereoAtoms indices."
                )
            bond = editable.GetBondBetweenAtoms(start, end)
            bond.SetStereoAtoms(stereo_atoms[0], stereo_atoms[1])
            bond.SetStereo(stereo_types[stereo])

    molecule = editable.GetMol()
    for atom_index in aromatic_atom_indices:
        molecule.GetAtomWithIdx(atom_index).SetIsAromatic(True)

    try:
        Chem.SanitizeMol(molecule)
    except Exception as error:
        raise GeometryInputError(f"Invalid molecular graph: {error}") from error
    return molecule


def _molecule_from_request(payload: dict[str, Any]) -> tuple[Chem.Mol, str, list[str]]:
    sources = [
        key for key in ("iupacName", "smiles", "molblock", "graph") if key in payload
    ]
    if len(sources) != 1:
        raise GeometryInputError(
            "Provide exactly one of iupacName, smiles, molblock, or graph."
        )

    source = sources[0]
    parsing_warnings: list[str] = []
    try:
        if source == "iupacName":
            molecule, parsing_warnings = _molecule_from_iupac_name(
                payload["iupacName"]
            )
        elif source == "smiles":
            value = payload["smiles"]
            if not isinstance(value, str) or not value.strip() or len(value) > 100_000:
                raise GeometryInputError("SMILES must be a non-empty string of at most 100,000 characters.")
            molecule = Chem.MolFromSmiles(value.strip(), sanitize=True)
            if molecule is None:
                raise GeometryInputError("RDKit could not parse or sanitize the supplied SMILES.")
        elif source == "molblock":
            value = payload["molblock"]
            if not isinstance(value, str) or not value.strip() or len(value) > MAX_REQUEST_BYTES:
                raise GeometryInputError("Molfile must be a non-empty string within the request size limit.")
            molecule = Chem.MolFromMolBlock(
                value,
                sanitize=True,
                removeHs=False,
                strictParsing=True,
            )
            if molecule is None:
                raise GeometryInputError("RDKit could not parse or sanitize the supplied molfile.")
        else:
            value = payload["graph"]
            if not isinstance(value, dict):
                raise GeometryInputError("Graph must be an object.")
            molecule = _molecule_from_graph(value)
    except (GeometryInputError, GeometryEngineUnavailableError):
        raise
    except Exception as error:
        raise GeometryInputError(f"Could not interpret the supplied molecular structure: {error}") from error

    heavy_atom_count = molecule.GetNumHeavyAtoms()
    if heavy_atom_count == 0:
        is_molecular_hydrogen = (
            molecule.GetNumAtoms() == 2
            and molecule.GetNumBonds() == 1
            and all(atom.GetAtomicNum() == 1 for atom in molecule.GetAtoms())
            and molecule.GetBondWithIdx(0).GetBondType() == Chem.BondType.SINGLE
        )
        if not is_molecular_hydrogen:
            raise GeometryInputError(
                "Hydrogen-only structures are supported only for bonded H2."
            )
    if heavy_atom_count > MAX_HEAVY_ATOMS:
        raise GeometryInputError(
            f"This endpoint supports up to {MAX_HEAVY_ATOMS} heavy atoms per molecule; "
            f"the input contains {heavy_atom_count}."
        )
    return molecule, source, parsing_warnings


def _optimize_conformers(
    molecule: Chem.Mol, force_field_request: str
) -> tuple[str, list[tuple[int, float]]]:
    if force_field_request not in ("auto", "MMFF94", "MMFF94s", "UFF"):
        raise GeometryInputError("forceField must be auto, MMFF94, MMFF94s, or UFF.")

    has_mmff = AllChem.MMFFHasAllMoleculeParams(molecule)
    has_uff = AllChem.UFFHasAllMoleculeParams(molecule)

    if force_field_request == "auto":
        force_field = "MMFF94s" if has_mmff else ("UFF" if has_uff else None)
    elif force_field_request in ("MMFF94", "MMFF94s"):
        force_field = force_field_request if has_mmff else None
    else:
        force_field = "UFF" if has_uff else None

    if force_field is None:
        raise GeometryInputError(
            "No requested supported force field has parameters for every atom in this molecule. "
            "This chemical class needs another validated geometry method."
        )

    if force_field == "UFF":
        results = AllChem.UFFOptimizeMoleculeConfs(
            molecule,
            numThreads=1,
            maxIters=500,
            ignoreInterfragInteractions=True,
        )
    else:
        results = AllChem.MMFFOptimizeMoleculeConfs(
            molecule,
            numThreads=1,
            maxIters=500,
            mmffVariant=force_field,
            ignoreInterfragInteractions=True,
        )
    return force_field, [(int(status), float(energy)) for status, energy in results]


def generate_geometry(payload: dict[str, Any]) -> dict[str, Any]:
    molecule, source, parsing_warnings = _molecule_from_request(payload)
    spin_multiplicity = payload.get("spinMultiplicity")
    if spin_multiplicity is not None and (
        isinstance(spin_multiplicity, bool)
        or not isinstance(spin_multiplicity, int)
        or spin_multiplicity < 1
    ):
        raise GeometryInputError("spinMultiplicity must be a positive integer.")

    Chem.AssignStereochemistry(molecule, force=True, cleanIt=True)
    expected_atom_stereo = {
        atom.GetIdx(): atom.GetProp("_CIPCode")
        for atom in molecule.GetAtoms()
        if atom.HasProp("_CIPCode")
    }
    expected_bond_stereo = {
        bond.GetIdx(): str(bond.GetStereo())
        for bond in molecule.GetBonds()
        if str(bond.GetStereo()) != "STEREONONE"
    }
    unassigned_centers = [
        atom_index
        for atom_index, label in Chem.FindMolChiralCenters(
            molecule, includeUnassigned=True, includeCIP=True
        )
        if label == "?"
    ]
    identity_molecule = Chem.Mol(molecule)
    seed = payload.get("seed", DEFAULT_RANDOM_SEED)
    if isinstance(seed, bool) or not isinstance(seed, int) or not 1 <= seed <= 2_147_483_647:
        raise GeometryInputError("seed must be an integer from 1 to 2,147,483,647.")

    conformer_count = payload.get("conformers", 8)
    if (
        isinstance(conformer_count, bool)
        or not isinstance(conformer_count, int)
        or not 1 <= conformer_count <= 20
    ):
        raise GeometryInputError("conformers must be an integer from 1 to 20.")

    molecule = Chem.AddHs(molecule, addCoords=False)
    if spin_multiplicity is not None:
        electron_count = sum(
            atom.GetAtomicNum() - atom.GetFormalCharge()
            for atom in molecule.GetAtoms()
        )
        if spin_multiplicity > electron_count + 1 or (
            (electron_count - spin_multiplicity + 1) % 2 != 0
        ):
            raise GeometryInputError(
                "spinMultiplicity is inconsistent with the molecule's electron count."
            )

    parameters = AllChem.ETKDGv3()
    parameters.randomSeed = seed
    parameters.numThreads = 1
    parameters.clearConfs = True
    conformer_ids = list(
        AllChem.EmbedMultipleConfs(molecule, numConfs=conformer_count, params=parameters)
    )
    if not conformer_ids:
        raise GeometryInputError(
            "ETKDGv3 could not generate a 3D conformer for this structure. "
            "Check its connectivity, stereochemistry, and ring constraints."
        )

    requested_force_field = payload.get("forceField", "auto")
    if not isinstance(requested_force_field, str):
        raise GeometryInputError("forceField must be a string.")
    force_field, results = _optimize_conformers(molecule, requested_force_field)
    viable = [
        (conformer_id, status, energy)
        for conformer_id, (status, energy) in zip(conformer_ids, results)
        if math.isfinite(energy)
    ]
    if not viable:
        raise GeometryInputError(f"{force_field} optimization produced no finite conformer energies.")

    chosen_id, status, energy = min(viable, key=lambda result: result[2])
    conformer = molecule.GetConformer(chosen_id)
    coordinates = [
        conformer.GetAtomPosition(atom.GetIdx()) for atom in molecule.GetAtoms()
    ]
    if any(
        not all(math.isfinite(value) for value in (point.x, point.y, point.z))
        for point in coordinates
    ):
        raise GeometryInputError(
            f"{force_field} optimization produced non-finite atom coordinates."
        )
    Chem.AssignStereochemistryFrom3D(
        molecule, confId=chosen_id, replaceExistingTags=True
    )
    Chem.AssignStereochemistry(molecule, force=True, cleanIt=True)
    actual_atom_stereo = {
        atom.GetIdx(): atom.GetProp("_CIPCode")
        for atom in molecule.GetAtoms()
        if atom.HasProp("_CIPCode")
    }
    actual_bond_stereo = {
        bond.GetIdx(): str(bond.GetStereo())
        for bond in molecule.GetBonds()
        if str(bond.GetStereo()) != "STEREONONE"
    }
    if any(actual_atom_stereo.get(index) != label for index, label in expected_atom_stereo.items()) or any(
        actual_bond_stereo.get(index) != label
        for index, label in expected_bond_stereo.items()
    ):
        raise GeometryInputError(
            "The generated conformer did not preserve the input's specified stereochemistry."
        )

    atoms = []
    for atom in molecule.GetAtoms():
        point = conformer.GetAtomPosition(atom.GetIdx())
        atoms.append(
            {
                "index": atom.GetIdx(),
                "element": atom.GetSymbol(),
                "atomicNumber": atom.GetAtomicNum(),
                "formalCharge": atom.GetFormalCharge(),
                "radicalElectrons": atom.GetNumRadicalElectrons(),
                "isotope": atom.GetIsotope(),
                "aromatic": atom.GetIsAromatic(),
                "stereochemistry": expected_atom_stereo.get(atom.GetIdx()),
                "position": {"x": point.x, "y": point.y, "z": point.z},
            }
        )

    bonds = []
    for bond in molecule.GetBonds():
        bonds.append(
            {
                "from": bond.GetBeginAtomIdx(),
                "to": bond.GetEndAtomIdx(),
                "order": 1.5 if bond.GetIsAromatic() else bond.GetBondTypeAsDouble(),
                "aromatic": bond.GetIsAromatic(),
                "stereochemistry": expected_bond_stereo.get(
                    bond.GetIdx(), "STEREONONE"
                ),
            }
        )

    warnings = [
        "Coordinates are a force-field-minimized conformer, not an experimental or quantum-chemical geometry.",
        "The lowest-energy conformer found in this bounded ETKDG ensemble is not guaranteed to be the global minimum.",
    ]
    warnings.extend(parsing_warnings)
    if unassigned_centers:
        warnings.append(
            "The input has unspecified stereocentres at atom indices "
            + ", ".join(str(index) for index in unassigned_centers)
            + "; no unique stereochemical configuration was supplied."
        )
    if force_field == "UFF":
        warnings.append(
            "UFF was used because the requested MMFF force field lacks parameters for this structure; "
            "UFF has different accuracy and parameter coverage."
        )
    radical_count = sum(atom.GetNumRadicalElectrons() for atom in molecule.GetAtoms())
    if radical_count:
        warnings.append(
            f"The input contains {radical_count} unpaired electron(s); the force field does not model "
            "electronic-state changes or reaction chemistry."
        )
    if spin_multiplicity is not None:
        warnings.append(
            f"Spin multiplicity {spin_multiplicity} is recorded but not used to parameterize the force field."
        )
    if status != 0:
        warnings.append(
            f"The selected force-field optimization did not converge within 500 iterations (status {status})."
        )
    component_count = len(Chem.GetMolFrags(molecule))
    if component_count > 1:
        warnings.append(
            "The input contains disconnected components. Their relative placement is not a prediction "
            "of ion pairing, solvation, or crystal packing."
        )

    molecule_without_hydrogens = Chem.RemoveHs(identity_molecule)
    from api.structure_naming import name_structure

    return {
        "atoms": atoms,
        "bonds": bonds,
        "depictionSvg": render_2d_svg(molecule_without_hydrogens),
        **name_structure(molecule_without_hydrogens),
        "metadata": {
            "inputFormat": source,
            "nameResolutionEngine": "OPSIN 2.9.0 (local)"
            if source == "iupacName"
            else None,
            "canonicalSmiles": Chem.MolToSmiles(molecule_without_hydrogens, isomericSmiles=True),
            "formula": rdMolDescriptors.CalcMolFormula(molecule_without_hydrogens),
            "molecularWeight": round(Descriptors.MolWt(molecule_without_hydrogens), 4),
            "formalCharge": sum(
                atom.GetFormalCharge() for atom in molecule_without_hydrogens.GetAtoms()
            ),
            "stereochemistry": [
                {"atomIndex": atom.GetIdx(), "label": atom.GetProp("_CIPCode")}
                for atom in molecule_without_hydrogens.GetAtoms()
                if atom.HasProp("_CIPCode")
            ],
            "unspecifiedStereocentres": unassigned_centers,
            "bondStereochemistry": [
                {"bondIndex": bond.GetIdx(), "label": str(bond.GetStereo())}
                for bond in molecule_without_hydrogens.GetBonds()
                if bond.GetStereo() != Chem.BondStereo.STEREONONE
            ],
            "coordinateUnit": "angstrom",
            "geometryMethod": "RDKit ETKDGv3 conformer generation and force-field minimization",
            "forceField": force_field,
            "forceFieldEnergyKcalMol": energy,
            "optimizationConverged": status == 0,
            "conformersGenerated": len(conformer_ids),
            "randomSeed": seed,
            "components": component_count,
            "stereochemistryChecked": True,
            "spinMultiplicity": spin_multiplicity,
            "warnings": warnings,
        },
    }


class handler(BaseHTTPRequestHandler):
    def _is_reaction_planner_request(self) -> bool:
        return parse_qs(urlsplit(self.path).query).get("service") == ["reaction_planner"]

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
        if self._is_reaction_planner_request():
            from chemistry.reaction_planner import handler as reaction_handler

            reaction_handler.do_GET(self)
            return

        self._atomview_request_id = uuid.uuid4().hex
        self._send_json(
            200,
            {
                "status": "ready",
                "engine": "RDKit ETKDGv3",
                "nameParser": "OPSIN 2.9.0 (local)",
            },
        )

    def do_POST(self) -> None:
        if self._is_reaction_planner_request():
            from chemistry.reaction_planner import handler as reaction_handler

            reaction_handler.do_POST(self)
            return

        self._atomview_request_id = uuid.uuid4().hex
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_error(400, "invalid_request", "Invalid Content-Length header.", "user-input")
            return
        if content_length <= 0:
            self._send_error(400, "missing_request_body", "A JSON request body is required.", "user-input")
            return
        if content_length > MAX_REQUEST_BYTES:
            self._send_error(413, "request_too_large", "Request body exceeds the 1 MB limit.", "user-input")
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
            if not isinstance(payload, dict):
                raise GeometryInputError("The JSON request body must be an object.")
            self._send_json(200, generate_geometry(payload))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            self._send_error(400, "invalid_json", "Request body must be valid JSON.", "user-input")
        except GeometryInputError as error:
            self._send_error(422, "invalid_structure", str(error), "invalid-structure")
        except GeometryEngineUnavailableError:
            self._send_error(
                503,
                "chemistry_engine_unavailable",
                "The local chemistry engine is temporarily unavailable.",
                "internal",
            )
        except Exception as error:
            _LOGGER.exception(
                "Geometry generation failed request_id=%s",
                self._atomview_request_id,
                exc_info=error,
            )
            self._send_error(
                500,
                "internal_error",
                "The geometry service could not complete this request.",
                "internal",
            )

    def _send_error(
        self, status_code: int, code: str, message: str, kind: str, **extra: Any
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
        service = "Reaction planner" if self._is_reaction_planner_request() else "Geometry"
        print(f"{service} API: {format % args}")
