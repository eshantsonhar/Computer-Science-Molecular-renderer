import io
import sys
import tarfile
from pathlib import Path


LIBRARIES = {
    "libXrender.so.1.3.0",
    "libX11.so.6.4.0",
    "libXext.so.6.4.0",
    "libxcb.so.1.1.0",
    "libXau.so.6.0.0",
    "libXdmcp.so.6.0.0",
    "libbsd.so.0.11.3",
    "libmd.so.0.0.4",
}


def debian_data_archive(package_path: Path) -> bytes:
    package = package_path.read_bytes()
    if not package.startswith(b"!<arch>\n"):
        raise ValueError(f"{package_path.name} is not a Debian archive.")

    offset = 8
    while offset < len(package):
        header = package[offset : offset + 60]
        if len(header) != 60 or header[58:60] != b"`\n":
            raise ValueError(f"{package_path.name} contains an invalid archive member.")
        name = header[:16].decode("ascii").strip().rstrip("/")
        size = int(header[48:58].decode("ascii").strip())
        content = package[offset + 60 : offset + 60 + size]
        if len(content) != size:
            raise ValueError(f"{package_path.name} contains a truncated archive member.")
        offset += 60 + size + size % 2
        if name.startswith("data.tar"):
            return content

    raise ValueError(f"{package_path.name} does not contain its data archive.")


def main() -> None:
    destination = Path(sys.argv[1])
    package_paths = [Path(argument) for argument in sys.argv[2:]]
    if not package_paths:
        raise ValueError("At least one Debian package is required.")

    destination.mkdir(parents=True, exist_ok=True)
    extracted: set[str] = set()
    notices = []
    for package_path in package_paths:
        with tarfile.open(fileobj=io.BytesIO(debian_data_archive(package_path)), mode="r:*") as archive:
            for member in archive.getmembers():
                filename = Path(member.name).name
                if member.isfile() and filename in LIBRARIES:
                    source = archive.extractfile(member)
                    if source is None:
                        raise ValueError(f"Could not read {filename} from {package_path.name}.")
                    (destination / filename).write_bytes(source.read())
                    extracted.add(filename)
                elif member.isfile() and member.name.endswith("/copyright"):
                    source = archive.extractfile(member)
                    if source is not None:
                        notices.append(f"## {package_path.name}\n{source.read().decode('utf-8')}")

    missing = LIBRARIES - extracted
    if missing:
        raise ValueError(f"Debian packages did not provide required libraries: {sorted(missing)}")
    (destination / "NOTICE.txt").write_text(
        "\n\n".join(notices) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
