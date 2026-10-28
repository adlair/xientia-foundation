import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "uno"))
from validate_uno_r2 import compare_document_content

COMMIT = "f92d3a47a4d65d451eb95e3686fb7f5147b98163"
META = "Versión general: 0.1.0 · Estado: draft · Commit: " + COMMIT[:12]

def sample():
    return {"content": ["Constitución de Xientia", META, "Artículo 1. Naturaleza", "Texto íntegro"]}

class IntegrityTests(unittest.TestCase):
    def test_identical_text(self):
        compare_document_content(sample(), sample(), COMMIT)

    def test_normative_change_rejected(self):
        altered = sample()
        altered["content"][-1] = "Texto alterado"
        with self.assertRaisesRegex(ValueError, "Diferencia"):
            compare_document_content(altered, sample(), COMMIT)

    def test_missing_paragraph_rejected(self):
        altered = sample()
        altered["content"].pop()
        with self.assertRaisesRegex(ValueError, "Cantidad"):
            compare_document_content(altered, sample(), COMMIT)

    def test_wrong_commit_rejected(self):
        with self.assertRaisesRegex(ValueError, "Commit"):
            compare_document_content(sample(), sample(), "0"*40)

    def test_checks_survive_python_optimized(self):
        source = (ROOT / "uno" / "validate_uno_r2.py").read_text()
        self.assertNotIn("assert ", source)
        code = (
            "import sys;sys.path.insert(0,%r);"
            "from validate_uno_r2 import compare_document_content;"
            "a={'content':['Versión general: 0.1.0 · Estado: draft · Commit: f92d3a47a4d6','CAMBIO']};"
            "b={'content':['Versión general: 0.1.0 · Estado: draft · Commit: f92d3a47a4d6','ORIGINAL']};"
            "compare_document_content(a,b)"
        ) % str(ROOT / "uno")
        result = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ValueError", result.stderr)

if __name__ == "__main__":
    unittest.main()
