"""Read-only reproducibility comparison for Xientia packages."""

import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

import pymupdf
from lxml import etree

EDITORIAL = Path(__file__).resolve().parent
sys.path.insert(0, str(EDITORIAL / "ci"))

from evidence_verify import verify_package, sha256_file


VOLATILE_METADATA = frozenset({
    "{urn:oasis:names:tc:opendocument:xmlns:meta:1.0}creation-date",
    "{http://purl.org/dc/elements/1.1/}date",
})

ZIP_ATTRIBUTES = (
    "compress_type",
    "flag_bits",
    "external_attr",
    "internal_attr",
    "create_system",
    "extra",
    "comment",
)


def load_verified_package(repo, root):
    """Verify a package before using any of its artifacts."""
    root = Path(root).resolve(strict=True)
    evidence_path = root / "evidence.json"

    if evidence_path.is_symlink():
        raise ValueError("Symlink evidence rejected")

    evidence = json.loads(
        evidence_path.read_text(encoding="utf-8")
    )
    verification = verify_package(repo, root, evidence)

    return {
        "root": root,
        "evidence": evidence,
        "verification": verification,
    }


def pdf_page_text(path):
    with pymupdf.open(path) as document:
        return [page.get_text(sort=False) for page in document]


def normalized_metadata(data):
    root = etree.fromstring(data)

    for element in root.iter():
        if element.tag in VOLATILE_METADATA:
            element.text = ""

    return etree.tostring(root, method="c14n")


def odt_component_comparison(path_a, path_b):
    """Compare ODT components, excluding approved volatile dates."""
    with ZipFile(path_a) as a, ZipFile(path_b) as b:
        names_a = a.namelist()
        names_b = b.namelist()

        if len(names_a) != len(set(names_a)):
            raise ValueError("Duplicate ODT entries in package A")

        if len(names_b) != len(set(names_b)):
            raise ValueError("Duplicate ODT entries in package B")

        missing_or_extra = sorted(set(names_a) ^ set(names_b))
        different = []
        metadata_differences = []

        if a.comment != b.comment:
            metadata_differences.append({
                "member": "<archive>",
                "attributes": ["comment"],
            })

        for name in sorted(set(names_a) & set(names_b)):
            info_a = a.getinfo(name)
            info_b = b.getinfo(name)

            changed = [
                attr for attr in ZIP_ATTRIBUTES
                if getattr(info_a, attr) != getattr(info_b, attr)
            ]

            if changed:
                metadata_differences.append({
                    "member": name,
                    "attributes": changed,
                })

            data_a = a.read(name)
            data_b = b.read(name)

            if name == "meta.xml":
                data_a = normalized_metadata(data_a)
                data_b = normalized_metadata(data_b)

            if data_a != data_b:
                different.append(name)

        return {
            "passed": not (
                missing_or_extra or different or metadata_differences
            ),
            "different_members": sorted(
                set(missing_or_extra) | set(different)
            ),
            "zip_metadata_differences": metadata_differences,
            "zip_order_identical": names_a == names_b,
        }


def compare_packages(repo, package_a, package_b):
    """Compare two verified packages from the same Git commit."""
    repo = Path(repo).resolve(strict=True)

    a = load_verified_package(repo, package_a)
    b = load_verified_package(repo, package_b)

    volume = a["verification"]["document"]

    if b["verification"]["document"] != volume:
        raise ValueError("Package volume mismatch")

    commit = a["verification"]["git_commit"]

    if b["verification"]["git_commit"] != commit:
        raise ValueError("Package Git commit mismatch")

    def artifact(package, kind):
        return (
            package["root"]
            / package["evidence"]["artifacts"][kind]["path"]
        )

    paths = {
        kind: (artifact(a, kind), artifact(b, kind))
        for kind in ("markdown", "odt", "pdf")
    }

    paths["manifest"] = (
        a["root"] / "manifest.json",
        b["root"] / "manifest.json",
    )
    paths["evidence"] = (
        a["root"] / "evidence.json",
        b["root"] / "evidence.json",
    )

    paths["manifest"] = (
        a["root"] / "manifest.json",
        b["root"] / "manifest.json",
    )
    paths["evidence"] = (
        a["root"] / "evidence.json",
        b["root"] / "evidence.json",
    )

    initial_hashes = {
        kind: tuple(sha256_file(p) for p in pair)
        for kind, pair in paths.items()
    }

    markdown_equal = (
        initial_hashes["markdown"][0]
        == initial_hashes["markdown"][1]
    )

    pages_a = pdf_page_text(paths["pdf"][0])
    pages_b = pdf_page_text(paths["pdf"][1])

    odt_result = odt_component_comparison(*paths["odt"])

    # Recheck all five files in both verified packages.
    for kind, pair in paths.items():
        if tuple(sha256_file(p) for p in pair) != initial_hashes[kind]:
            raise ValueError(
                f"Artifact changed during comparison: {kind}"
            )

    return {
        "phase": "F4.4-R1",
        "document": volume,
        "git_commit": commit,
        "packages_verified": 2,
        "levels": {
            "L1": {
                "passed": markdown_equal and pages_a == pages_b,
                "markdown_identical": markdown_equal,
                "pdf_text_identical": pages_a == pages_b,
                "pages_a": len(pages_a),
                "pages_b": len(pages_b),
            },
            "L2": odt_result,
        },
    }
