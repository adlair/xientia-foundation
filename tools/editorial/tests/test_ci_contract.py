"""Tests for the Xientia Editorial CI policy contract."""

import copy
import importlib.util
import json
import unittest
from pathlib import Path

EDITORIAL = Path(__file__).resolve().parents[1]
VALIDATOR = EDITORIAL / "ci/validate_ci_contract.py"
CONTRACT = EDITORIAL / "ci/editorial_ci_contract.json"

spec = importlib.util.spec_from_file_location(
    "xientia_ci_contract", VALIDATOR
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(
            CONTRACT.read_text(encoding="utf-8")
        )

    def test_valid_contract(self):
        self.assertTrue(
            module.validate_contract(self.contract)
        )

    def test_institutional_adoption_rejected(self):
        modified = copy.deepcopy(self.contract)
        modified["publication"]["institutional_adoption"] = True

        with self.assertRaises(ValueError):
            module.validate_contract(modified)

    def test_automatic_release_rejected(self):
        modified = copy.deepcopy(self.contract)
        modified["ci"]["main"][
            "publish_institutional_release"
        ] = True

        with self.assertRaises(ValueError):
            module.validate_contract(modified)

    def test_missing_hash_rejected(self):
        modified = copy.deepcopy(self.contract)
        modified["traceability"]["require_sha256"] = [
            "markdown", "odt"
        ]

        with self.assertRaises(ValueError):
            module.validate_contract(modified)

    def test_unknown_volume_rejected(self):
        modified = copy.deepcopy(self.contract)
        modified["supported_volumes"].append("UNKNOWN")

        with self.assertRaises(ValueError):
            module.validate_contract(modified)

    def test_disabled_provenance_rejected(self):
        modified = copy.deepcopy(self.contract)
        modified["traceability"]["require_git_commit"] = False

        with self.assertRaises(ValueError):
            module.validate_contract(modified)


if __name__ == "__main__":
    unittest.main()
