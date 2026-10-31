"""F4.3 R2-B2: construct real editorial evidence in memory."""

import json
import subprocess
import sys
from pathlib import Path

CI = Path(__file__).resolve().parent
EDITORIAL = CI.parent

sys.path.insert(0, str(CI))
sys.path.insert(0, str(EDITORIAL))

from evidence_schema import validate_evidence
from evidence_verify import (
    git_commit,
    git_status,
    sha256_file,
    verify_package,
)
from odt_structure import validate_odt
from pdf_correspondence import validate_odt_pdf


def command_version(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    value = result.stdout.strip()

    if not value:
        raise ValueError("Empty tool version")

    return value.splitlines()[0]


def tool_versions():
    import pymupdf

    return {
        "python": sys.version.split()[0],
        "libreoffice": command_version(
            ["libreoffice", "--version"]
        ),
        "pandoc": command_version(
            ["pandoc", "--version"]
        ),
        "pymupdf": pymupdf.VersionBind,
    }


def generate_evidence(repo, root, volume):
    """Build and verify evidence without writing any files."""

    repo = Path(repo).resolve(strict=True)
    root = Path(root).resolve(strict=True)

    if volume not in ("XV-001", "XEP-0000"):
        raise ValueError("Unsupported evidence volume")

    if git_status(repo):
        raise ValueError("Dirty repository rejected")

    manifest = json.loads(
        (root / "manifest.json").read_text(encoding="utf-8")
    )

    commit = git_commit(repo)

    if manifest.get("document") != volume:
        raise ValueError("Manifest volume mismatch")

    if manifest.get("git_commit") != commit:
        raise ValueError("Manifest Git commit mismatch")

    paths = {
        "markdown": f"{volume}_consulta.md",
        "odt": f"{volume}_consulta.odt",
        "pdf": f"pdf/{volume}_consulta.pdf",
    }

    artifacts = {
        kind: {
            "path": relative,
            "sha256": sha256_file(root / relative),
        }
        for kind, relative in paths.items()
    }

    odt = root / paths["odt"]
    pdf = root / paths["pdf"]

    structure = validate_odt(volume, odt)
    correspondence = validate_odt_pdf(volume, odt, pdf)

    evidence = {
        "schema_version": "1.0.0",
        "phase": "F4.3-R2",
        "document": volume,
        "status": "draft",
        "edition": "consulta-no-adoptada",
        "institutional_adoption": False,
        "provenance": {
            "git_commit": commit,
            "dirty_tracked": False,
        },
        "artifacts": artifacts,
        "tools": tool_versions(),
        "validation": {
            "odt_structure": {
                "passed": True,
                "details": structure,
            },
            "pdf_correspondence": {
                "passed": True,
                "details": correspondence,
            },
        },
    }

    validate_evidence(evidence)
    verify_package(repo, root, evidence)

    return evidence


def write_evidence(root, evidence):
    """Write validated evidence without replacing existing files."""

    import os
    import tempfile

    root = Path(root).resolve(strict=True)

    validate_evidence(evidence)

    destination = root / "evidence.json"

    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)

    payload = (
        json.dumps(
            evidence,
            ensure_ascii=False,
            indent=2,
        ) + "\n"
    ).encode("utf-8")

    temporary = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".xientia-evidence-",
            suffix=".tmp",
            dir=root,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())

        # Atomic no-replace publication on the same filesystem.
        os.link(temporary, destination)

        written = destination.read_bytes()

        if written != payload:
            raise RuntimeError("Evidence write verification failed")

        return destination

    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def generate_and_write_evidence(repo, root, volume):
    """Generate, verify and exclusively write consultation evidence."""

    repo = Path(repo).resolve(strict=True)
    root = Path(root).resolve(strict=True)

    destination = root / "evidence.json"

    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)

    evidence = generate_evidence(repo, root, volume)

    # Recheck the package immediately before writing.
    verify_package(repo, root, evidence)

    return write_evidence(root, evidence)
