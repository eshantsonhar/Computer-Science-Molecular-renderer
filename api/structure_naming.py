import logging
import os
import shutil
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

from api.geometry import Chem


_LOGGER = logging.getLogger(__name__)
_ENGINE_LOCK = threading.Lock()
_ENGINE: Any = None
_REPORTED_UNAVAILABLE: set[str] = set()
_UNAVAILABLE_NAME = "IUPAC name unavailable for this structure"
_ORTHONYM_JARS = Path(__file__).parent / "vendor" / "orthonym_jars"


def _unavailable(reason: str) -> dict[str, Any]:
    return {
        "name": _UNAVAILABLE_NAME,
        "iupacName": None,
        "naming": {
            "engine": "Orthonym 1.1.0",
            "status": "unavailable",
            "tier": "abstain",
            "verified": False,
            "reason": reason,
        },
    }


def _report_unavailable_once(reason: str, message: str) -> None:
    with _ENGINE_LOCK:
        if reason in _REPORTED_UNAVAILABLE:
            return
        _REPORTED_UNAVAILABLE.add(reason)
    _LOGGER.error("%s", message)


def _configure_local_engine() -> None:
    opsin_jar = _ORTHONYM_JARS / "opsin-cli-2.9.0-jar-with-dependencies.jar"
    centres_jar = _ORTHONYM_JARS / "centres-cli-1.2.1.jar"
    if not opsin_jar.is_file() or not centres_jar.is_file():
        raise FileNotFoundError("Pinned local Orthonym naming resources are missing.")

    os.environ["ORTHONYM_OPSIN_JAR"] = str(opsin_jar)
    os.environ["ORTHONYM_CENTRES_JAR"] = str(centres_jar)
    os.environ["ORTHONYM_NO_DOWNLOAD"] = "1"
    os.environ["ORTHONYM_DISABLE_JPYPE"] = "1"

    from api.geometry import GeometryEngineUnavailableError, _opsin_java_executable

    try:
        java = _opsin_java_executable(Path(__file__).parent / "vendor" / "opsin")
    except GeometryEngineUnavailableError as error:
        raise FileNotFoundError("The bundled local Java runtime could not be prepared.") from error
    if java:
        java_directory = str(Path(java).parent)
        os.environ.setdefault("JAVA_HOME", str(Path(java).parent.parent))
        if java_directory not in os.environ.get("PATH", "").split(os.pathsep):
            os.environ["PATH"] = java_directory + os.pathsep + os.environ.get("PATH", "")
    elif shutil.which("java") is None:
        raise FileNotFoundError("A local Java runtime is required by Orthonym.")


def _same_isomeric_structure(first: Chem.Mol, second: Chem.Mol) -> bool:
    return Chem.MolToSmiles(
        first, canonical=True, isomericSmiles=True
    ) == Chem.MolToSmiles(second, canonical=True, isomericSmiles=True)


@lru_cache(maxsize=512)
def _name_canonical_smiles(smiles: str) -> dict[str, Any]:
    molecule = Chem.MolFromSmiles(smiles, sanitize=True)
    if molecule is None:
        raise ValueError("The validated molecule could not be reconstructed for naming.")

    try:
        _configure_local_engine()
    except (FileNotFoundError, OSError) as error:
        _report_unavailable_once(
            "local-naming-runtime-unavailable",
            f"Orthonym naming is unavailable: {error}",
        )
        return _unavailable("local-naming-runtime-unavailable")

    try:
        from orthonym import Orthonym, OrthonymLimitError
        from orthonym.jars import JarUnavailable
    except ModuleNotFoundError as error:
        if error.name != "orthonym":
            raise
        _report_unavailable_once(
            "local-naming-engine-not-installed",
            "Orthonym is not installed in the chemistry runtime.",
        )
        return _unavailable("local-naming-engine-not-installed")

    global _ENGINE
    try:
        if _ENGINE is None:
            with _ENGINE_LOCK:
                if _ENGINE is None:
                    _ENGINE = Orthonym()
        row = _ENGINE.name_tiered(smiles)
    except JarUnavailable as error:
        _report_unavailable_once(
            "local-naming-runtime-unavailable",
            f"Orthonym could not initialize its pinned local resources: {error}",
        )
        return _unavailable("local-naming-runtime-unavailable")
    except OrthonymLimitError as error:
        result = _unavailable("structure-outside-supported-nomenclature")
        result["naming"]["detail"] = str(error)
        return result

    tier = row.get("tier", "abstain")
    candidate = row.get("name")
    if not isinstance(candidate, str) or not candidate.strip():
        return _unavailable("naming-engine-abstained")

    if tier in {"pin_verified", "systematic_verified"}:
        if row.get("verified") != "opsin":
            return _unavailable("verified-tier-missing-opsin-confirmation")
        from api.geometry import GeometryInputError, _molecule_from_request

        try:
            reconstructed, _, _ = _molecule_from_request({"iupacName": candidate})
        except GeometryInputError:
            reconstructed = None
        if reconstructed is not None and _same_isomeric_structure(molecule, reconstructed):
            return {
                "name": candidate,
                "iupacName": candidate,
                "naming": {
                    "engine": "Orthonym 1.1.0",
                    "status": "verified",
                    "tier": tier,
                    "verified": True,
                    "verification": "OPSIN 2.9.0 round trip; canonical isomeric SMILES identity",
                },
            }

        _LOGGER.warning(
            "Rejected Orthonym name after exact OPSIN identity check; tier=%s",
            tier,
        )
        return _unavailable("opsin-round-trip-identity-mismatch")

    if tier == "abstain":
        return _unavailable("naming-engine-abstained")
    label = (
        "Unverified PIN candidate"
        if tier == "pin_unverified"
        else "Best-effort systematic name (not verified)"
    )
    return {
        "name": f"{label}: {candidate}",
        "iupacName": None,
        "naming": {
            "engine": "Orthonym 1.1.0",
            "status": "unverified",
            "tier": tier,
            "verified": False,
            "candidateName": candidate,
            "reason": "The generated name did not meet the verified naming tier.",
        },
    }


def name_structure(molecule: Chem.Mol) -> dict[str, Any]:
    if molecule is None or molecule.GetNumAtoms() == 0:
        raise ValueError("A non-empty, validated molecule is required for naming.")
    smiles = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
    return dict(_name_canonical_smiles(smiles))
