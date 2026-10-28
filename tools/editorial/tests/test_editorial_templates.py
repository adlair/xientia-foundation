import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from editorial_template import resolve_template

class TemplateTests(unittest.TestCase):
    def test_bundled_template_resolves(self):
        self.assertTrue(resolve_template(ROOT).is_file())

    def test_modified_template_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "templates" / "XF-000"
            folder.mkdir(parents=True)
            shutil.copy2(ROOT / "templates/XF-000/reference.odt", folder / "reference.odt")
            shutil.copy2(ROOT / "templates/XF-000/template.json", folder / "template.json")
            with (folder / "reference.odt").open("ab") as f:
                f.write(b"alteration")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                resolve_template(Path(d))

    def test_invalid_profile_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "templates" / "XF-000"
            folder.mkdir(parents=True)
            shutil.copy2(ROOT / "templates/XF-000/reference.odt", folder / "reference.odt")
            obj = json.loads((ROOT / "templates/XF-000/template.json").read_text())
            obj["volume"] = "XV-001"
            (folder / "template.json").write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError, "Perfil"):
                resolve_template(Path(d))

if __name__ == "__main__":
    unittest.main()
