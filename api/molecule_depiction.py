import ctypes
import sys
from pathlib import Path


_LINUX_DRAWING_LIBRARIES = (
    "libmd.so.0.0.4",
    "libbsd.so.0.11.3",
    "libXau.so.6.0.0",
    "libXdmcp.so.6.0.0",
    "libxcb.so.1.1.0",
    "libX11.so.6.4.0",
    "libXext.so.6.4.0",
    "libXrender.so.1.3.0",
)


def _preload_linux_drawing_libraries() -> None:
    if sys.platform != "linux":
        return

    library_directory = Path(__file__).resolve().parent / "vendor" / "rdkit_runtime_libs"
    if not library_directory.is_dir():
        return

    for library_name in _LINUX_DRAWING_LIBRARIES:
        library_path = library_directory / library_name
        if not library_path.is_file():
            raise RuntimeError(f"Required Linux drawing library is missing: {library_name}")
        ctypes.CDLL(str(library_path), mode=ctypes.RTLD_GLOBAL)


_preload_linux_drawing_libraries()

from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D


def render_2d_svg(molecule: Chem.Mol, width: int = 640, height: int = 420) -> str:
    if molecule is None or molecule.GetNumAtoms() == 0:
        raise ValueError("A non-empty, validated molecule is required for depiction.")

    depiction = Chem.Mol(molecule)
    rdDepictor.Compute2DCoords(
        depiction,
        canonOrient=True,
        clearConfs=True,
        forceRDKit=True,
    )
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    options = drawer.drawOptions()
    options.useBWAtomPalette()
    options.addStereoAnnotation = True
    options.clearBackground = True
    drawer.DrawMolecule(depiction)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    if "<svg" not in svg or "</svg>" not in svg:
        raise RuntimeError("RDKit did not produce a complete molecular SVG depiction.")
    return svg
