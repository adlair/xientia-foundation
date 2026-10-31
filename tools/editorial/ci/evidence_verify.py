"""F4.3 R2-B: verify real editorial evidence."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath

EDITORIAL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITORIAL))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from odt_structure import validate_odt
from pdf_correspondence import validate_odt_pdf
from evidence_schema import validate_evidence


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for block in iter(
            lambda: stream.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def git_commit(repo):
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
    ).strip()



def git_status(repo):
    return subprocess.check_output(
        [
            "git", "-C", str(repo),
            "status", "--porcelain",
        ],
        text=True,
    ).strip()


def verify_sources(repo, manifest):
    sources = manifest.get("sources")
    metadata = manifest.get("metadata_source")

    if not isinstance(sources, dict) or not sources:
        raise ValueError("Missing source hashes")

    if not isinstance(metadata, dict) or not metadata:
        raise ValueError("Missing metadata hashes")

    for group in (sources, metadata):
        for relative, expected in group.items():
            if not isinstance(relative, str):
                raise ValueError("Invalid source path")

            if not isinstance(expected, str):
                raise ValueError("Invalid source digest")

            if not relative or "\\" in relative:
                raise ValueError("Invalid source path")

            normalized = PurePosixPath(relative)

            if (
                normalized.is_absolute()
                or ".." in normalized.parts
                or "." in relative.split("/")
                or str(normalized) != relative
            ):
                raise ValueError("Noncanonical source path")

            candidate = repo / relative
            resolved = candidate.resolve(strict=True)

            if not resolved.is_relative_to(repo):
                raise ValueError("Source outside repository")

            if any(
                item.is_symlink()
                for item in (
                    candidate,
                    *candidate.parents
                )
                if item.is_relative_to(repo)
            ):
                raise ValueError("Symlink source rejected")

            if not resolved.is_file():
                raise ValueError("Source is not a regular file")

            if sha256_file(resolved) != expected:
                raise ValueError(
                    f"Source hash mismatch: {relative}"
                )

    return True



def verify_source_contract(repo, volume, manifest, commit):
    """Check exact source set and committed file contents."""

    profile_path = (
        repo / "tools/editorial/config" / f"{volume}.json"
    )

    profile_bytes = profile_path.read_bytes()

    committed_profile = subprocess.check_output(
        [
            "git", "-C", str(repo),
            "show",
            f"{commit}:tools/editorial/config/{volume}.json",
        ]
    )

    if profile_bytes != committed_profile:
        raise ValueError("Editorial profile Git mismatch")

    profile = json.loads(profile_bytes.decode("utf-8"))

    if profile.get("id") != volume:
        raise ValueError("Editorial profile mismatch")

    expected = []

    for key in (
        "prefix",
        "chapter_1_files",
        "chapter_files",
        "suffix",
    ):
        paths = profile.get(key, [])

        if not isinstance(paths, list):
            raise ValueError("Invalid editorial source list")

        expected.extend(paths)

    if len(expected) != len(set(expected)):
        raise ValueError("Duplicate editorial sources")

    if list(manifest["sources"]) != expected:
        raise ValueError("Editorial source set mismatch")

    metadata = profile.get("metadata")

    if list(manifest["metadata_source"]) != [metadata]:
        raise ValueError("Editorial metadata mismatch")

    if manifest.get("validation") != profile.get("validation"):
        raise ValueError("Editorial validation rule mismatch")

    all_sources = {
        **manifest["sources"],
        **manifest["metadata_source"],
    }

    for relative, expected_hash in all_sources.items():
        committed = subprocess.run(
            [
                "git", "-C", str(repo),
                "show", f"{commit}:{relative}",
            ],
            capture_output=True,
            check=True,
        ).stdout

        if hashlib.sha256(committed).hexdigest() != expected_hash:
            raise ValueError(
                f"Git committed source mismatch: {relative}"
            )

    return True


def verify_package(repo, root, evidence):
    repo = Path(repo).resolve(strict=True)
    root = Path(root).resolve(strict=True)

    validate_evidence(evidence)

    volume = evidence["document"]
    manifest_path = root / "manifest.json"

    if manifest_path.is_symlink():
        raise ValueError("Symlink manifest rejected")

    manifest_initial_hash = sha256_file(manifest_path)

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    if manifest.get("document") != volume:
        raise ValueError("Manifest volume mismatch")

    if (
        manifest.get("status") != "draft"
        or manifest.get("edition") != "consulta-no-adoptada"
    ):
        raise ValueError("Unsafe manifest status")

    if manifest.get("dirty_tracked") is not False:
        raise ValueError("Dirty manifest rejected")

    if git_status(repo):
        raise ValueError("Dirty repository rejected")

    commit = git_commit(repo)

    verify_source_contract(
        repo, volume, manifest, commit
    )

    verify_sources(repo, manifest)

    if manifest.get("git_commit") != commit:
        raise ValueError("Manifest Git commit mismatch")

    if evidence["provenance"]["git_commit"] != commit:
        raise ValueError("Evidence Git commit mismatch")

    artifacts = evidence["artifacts"]
    initial_hashes = {}
    verified_paths = {}

    for kind, artifact in artifacts.items():
        path = root / artifact["path"]

        if any(
            component.is_symlink()
            for component in (path, *path.parents)
            if component == root or component.is_relative_to(root)
        ):
            raise ValueError("Symlink artifact path rejected")

        resolved = path.resolve(strict=True)

        if not resolved.is_relative_to(root):
            raise ValueError("Artifact outside package")

        if not resolved.is_file():
            raise ValueError("Artifact is not a regular file")

        digest = sha256_file(resolved)

        if digest != artifact["sha256"]:
            raise ValueError(f"Artifact SHA-256 mismatch: {kind}")

        initial_hashes[kind] = digest
        verified_paths[kind] = resolved

    if manifest.get("output_sha256") != initial_hashes["markdown"]:
        raise ValueError("Manifest Markdown hash mismatch")

    odt = verified_paths["odt"]
    pdf = verified_paths["pdf"]

    structure = validate_odt(volume, odt)
    correspondence = validate_odt_pdf(volume, odt, pdf)

    if structure != evidence["validation"]["odt_structure"]["details"]:
        raise ValueError("ODT validation evidence mismatch")

    if correspondence != evidence["validation"]["pdf_correspondence"]["details"]:
        raise ValueError("PDF validation evidence mismatch")

    for kind, resolved in verified_paths.items():
        if sha256_file(resolved) != initial_hashes[kind]:
            raise ValueError(f"Artifact changed during validation: {kind}")

    if sha256_file(manifest_path) != manifest_initial_hash:
        raise ValueError("Manifest changed during validation")

    return {
        "document": volume,
        "git_commit": commit,
        "artifacts_verified": len(artifacts),
        "odt_structure": structure,
        "pdf_correspondence": correspondence,
    }
