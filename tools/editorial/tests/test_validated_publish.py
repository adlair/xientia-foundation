import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from validated_publish import publish_validated

class ValidatedPublishTests(unittest.TestCase):
    def args(self, repo, out, volume="XV-001"):
        return SimpleNamespace(repo=repo, out=out, volume=volume,
                               format="all", allow_dirty=True)

    def test_existing_output_not_replaced(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); repo=root/"repo"; repo.mkdir()
            out=root/"published"; out.mkdir()
            (out/"protected").write_text("safe")
            with self.assertRaises(FileExistsError):
                publish_validated(self.args(repo,out), ROOT/"render_library.py")
            self.assertEqual((out/"protected").read_text(),"safe")

    def test_reject_output_inside_repo(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d); out=repo/"output"
            with self.assertRaises(ValueError):
                publish_validated(self.args(repo,out), ROOT/"render_library.py")
            self.assertFalse(out.exists())

    def test_failed_validation_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); repo=root/"repo"; repo.mkdir(); out=root/"published"
            def fake_render(cmd, check):
                stage=Path(cmd[cmd.index("--out")+1]); stage.mkdir()
                (stage/"manifest.json").write_text(json.dumps({
                    "document":"XV-001","status":"draft","edition":"consulta-no-adoptada"
                }))
            with patch("validated_publish.subprocess.run",side_effect=fake_render):
                with self.assertRaises(FileNotFoundError):
                    publish_validated(self.args(repo,out), ROOT/"render_library.py")
            self.assertFalse(out.exists())
            self.assertFalse(list(root.glob(".xientia-f42-*")))

    def test_success_atomic_publish(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); repo=root/"repo"; repo.mkdir(); out=root/"published"
            def fake_render(cmd, check):
                stage=Path(cmd[cmd.index("--out")+1]); (stage/"pdf").mkdir(parents=True)
                (stage/"manifest.json").write_text(json.dumps({
                    "document":"XV-001","status":"draft","edition":"consulta-no-adoptada"
                }))
                (stage/"XV-001_consulta.odt").write_bytes(b"mock")
                (stage/"pdf/XV-001_consulta.pdf").write_bytes(b"mock")
            with patch("validated_publish.subprocess.run",side_effect=fake_render), \
                 patch("validated_publish.validate_odt",return_value={"chapters":15,"articles":0,"headings":142}), \
                 patch("validated_publish.validate_odt_pdf",return_value={"headings":142,"pages":52}):
                publish_validated(self.args(repo,out), ROOT/"render_library.py")
            self.assertTrue((out/"manifest.json").is_file())
            self.assertFalse(list(root.glob(".xientia-f42-*")))

if __name__=="__main__":
    unittest.main()
