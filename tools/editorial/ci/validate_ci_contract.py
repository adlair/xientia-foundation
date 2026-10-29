#!/usr/bin/env python3
"""Validate Xientia Editorial CI policy contract."""

import argparse
import json
from pathlib import Path

VOLUMES = ("XF-000", "XV-001", "XEP-0000")
HASHES = ("markdown", "odt", "pdf")


def validate_contract(contract):
    if not isinstance(contract, dict):
        raise ValueError("Contract must be an object")

    if contract.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported schema version")

    if contract.get("phase") != "F4.3-R0":
        raise ValueError("Unexpected phase")

    if contract.get("repository") != "xientia-foundation":
        raise ValueError("Unexpected repository")

    if contract.get("source_of_truth") != "markdown":
        raise ValueError("Markdown must remain authoritative")

    if contract.get("supported_volumes") != list(VOLUMES):
        raise ValueError("Unexpected volume contract")

    publication = contract.get("publication")
    if not isinstance(publication, dict):
        raise ValueError("Missing publication policy")

    expected_publication = {
        "allowed_document_status": "draft",
        "edition": "consulta-no-adoptada",
        "institutional_adoption": False,
        "allow_automatic_institutional_release": False,
    }

    if publication != expected_publication:
        raise ValueError("Unsafe publication policy")

    traceability = contract.get("traceability")
    if not isinstance(traceability, dict):
        raise ValueError("Missing traceability policy")

    required_true = (
        "require_git_commit",
        "require_clean_tree_for_release_build",
        "require_manifest",
        "require_tool_versions",
        "require_validation_report",
    )

    for field in required_true:
        if traceability.get(field) is not True:
            raise ValueError(f"Required traceability disabled: {field}")

    if traceability.get("require_sha256") != list(HASHES):
        raise ValueError("Incomplete hash requirements")

    ci = contract.get("ci")
    if not isinstance(ci, dict):
        raise ValueError("Missing CI policy")

    expected_ci = {
        "pull_request": {
            "run_tests": True,
            "publish_artifacts": False,
        },
        "main": {
            "run_tests": True,
            "build_consultation_editions": True,
            "publish_institutional_release": False,
        },
        "concurrency_audit": {
            "automatic_on_pull_request": False,
            "manual": True,
        },
    }

    if ci != expected_ci:
        raise ValueError("Unsafe CI policy")

    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    args = parser.parse_args()

    contract = json.loads(
        args.contract.read_text(encoding="utf-8")
    )

    validate_contract(contract)
    print("XIENTIA CI CONTRACT: VALID")


if __name__ == "__main__":
    main()
