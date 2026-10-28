import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UNOEntrypointTests(unittest.TestCase):

    def test_r4_help_executes(self):
        script = ROOT / "uno" / "update_toc_uno_r4.py"

        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--expected-commit", result.stdout)
        self.assertIn("--input", result.stdout)


if __name__ == "__main__":
    unittest.main()
