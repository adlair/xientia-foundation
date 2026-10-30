"""Tests for F4.3 R2-A evidence schema."""

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE = (
    Path(__file__).resolve().parents[1]
    / "ci/evidence_schema.py"
)

spec = importlib.util.spec_from_file_location(
    "xientia_evidence_schema", MODULE
)
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)


def valid_evidence(volume="XV-001"):
    return {
        "schema_version": "1.0.0",
        "phase": "F4.3-R2",
        "document": volume,
        "status": "draft",
        "edition": "consulta-no-adoptada",
        "institutional_adoption": False,
        "provenance": {
            "git_commit": "a" * 40,
            "dirty_tracked": False,
        },
        "artifacts": {
            "markdown": {
                "path": f"{volume}_consulta.md",
                "sha256": "b" * 64,
            },
            "odt": {
                "path": f"{volume}_consulta.odt",
                "sha256": "c" * 64,
            },
            "pdf": {
                "path": f"pdf/{volume}_consulta.pdf",
                "sha256": "d" * 64,
            },
        },
        "tools": {
            "python": "3.12.3",
            "libreoffice": "24.2.7",
            "pandoc": "3.1.3",
            "pymupdf": "1.26.7",
        },
        "validation": {
            "odt_structure": {
                "passed": True,
                "details": {"chapters": 15},
            },
            "pdf_correspondence": {
                "passed": True,
                "details": {"headings": 142},
            },
        },
    }


class EvidenceSchemaTests(unittest.TestCase):
    def test_valid_xv(self):
        self.assertTrue(schema.validate_evidence(valid_evidence()))

    def test_valid_xep(self):
        self.assertTrue(
            schema.validate_evidence(valid_evidence("XEP-0000"))
        )

    def test_institutional_adoption_rejected(self):
        data = valid_evidence()
        data["institutional_adoption"] = True
        with self.assertRaises(ValueError):
            schema.validate_evidence(data)

    def test_dirty_tree_rejected(self):
        data = valid_evidence()
        data["provenance"]["dirty_tracked"] = True
        with self.assertRaises(ValueError):
            schema.validate_evidence(data)

    def test_invalid_hash_rejected(self):
        data = valid_evidence()
        data["artifacts"]["pdf"]["sha256"] = "invalid"
        with self.assertRaises(ValueError):
            schema.validate_evidence(data)

    def test_path_traversal_rejected(self):
        data = valid_evidence()
        data["artifacts"]["pdf"]["path"] = "../outside.pdf"
        with self.assertRaises(ValueError):
            schema.validate_evidence(data)

    def test_unknown_volume_rejected(self):
        data = valid_evidence()
        data["document"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            schema.validate_evidence(data)

    def test_missing_tool_version_rejected(self):
        data = valid_evidence()
        data["tools"]["libreoffice"] = ""
        with self.assertRaises(ValueError):
            schema.validate_evidence(data)

    def test_failed_validation_rejected(self):
        data = valid_evidence()
        data["validation"]["odt_structure"]["passed"] = False
        with self.assertRaises(ValueError):
            schema.validate_evidence(data)


if __name__ == "__main__":
    unittest.main()
