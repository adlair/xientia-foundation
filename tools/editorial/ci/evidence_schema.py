"""F4.3 R2-A: strict schema for consultation evidence."""

import re
from pathlib import PurePosixPath

VOLUMES = ("XV-001", "XEP-0000")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")

TOOLS = ("python", "libreoffice", "pandoc", "pymupdf")
ARTIFACTS = ("markdown", "odt", "pdf")


def require_keys(obj, keys, name):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ValueError(f"Invalid {name}")


def validate_evidence(data):
    require_keys(
        data,
        (
            "schema_version",
            "phase",
            "document",
            "status",
            "edition",
            "institutional_adoption",
            "provenance",
            "artifacts",
            "tools",
            "validation",
        ),
        "evidence",
    )

    if data["schema_version"] != "1.0.0":
        raise ValueError("Unsupported schema")

    if data["phase"] != "F4.3-R2":
        raise ValueError("Unexpected phase")

    volume = data["document"]

    if volume not in VOLUMES:
        raise ValueError("Unsupported volume")

    if (
        data["status"] != "draft"
        or data["edition"] != "consulta-no-adoptada"
        or data["institutional_adoption"] is not False
    ):
        raise ValueError("Unsafe publication state")

    provenance = data["provenance"]

    require_keys(
        provenance,
        ("git_commit", "dirty_tracked"),
        "provenance",
    )

    if not isinstance(provenance["git_commit"], str):
        raise ValueError("Invalid Git commit")

    if not COMMIT.fullmatch(provenance["git_commit"]):
        raise ValueError("Invalid Git commit")

    if provenance["dirty_tracked"] is not False:
        raise ValueError("Dirty provenance rejected")

    artifacts = data["artifacts"]
    require_keys(artifacts, ARTIFACTS, "artifacts")

    expected_paths = {
        "markdown": f"{volume}_consulta.md",
        "odt": f"{volume}_consulta.odt",
        "pdf": f"pdf/{volume}_consulta.pdf",
    }

    for kind, artifact in artifacts.items():
        require_keys(
            artifact,
            ("path", "sha256"),
            f"artifact {kind}",
        )

        path = artifact["path"]
        digest = artifact["sha256"]

        if not isinstance(path, str):
            raise ValueError("Invalid artifact path")

        if PurePosixPath(path).is_absolute():
            raise ValueError("Absolute artifact path")

        if path != expected_paths[kind]:
            raise ValueError("Unexpected artifact path")

        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ValueError("Invalid SHA-256")

    tools = data["tools"]
    require_keys(tools, TOOLS, "tools")

    for name, version in tools.items():
        if not isinstance(version, str) or not version.strip():
            raise ValueError(f"Missing tool version: {name}")

    validation = data["validation"]

    require_keys(
        validation,
        ("odt_structure", "pdf_correspondence"),
        "validation",
    )

    for name, result in validation.items():
        require_keys(
            result,
            ("passed", "details"),
            name,
        )

        if result["passed"] is not True:
            raise ValueError(f"Validation not passed: {name}")

        if not isinstance(result["details"], dict) or not result["details"]:
            raise ValueError(f"Missing validation details: {name}")

    return True
