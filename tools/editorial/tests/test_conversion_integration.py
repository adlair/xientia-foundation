"""Integration tests for real Pandoc/LibreOffice conversion and failure cleanup."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[3]
RENDER = ROOT / "tools/editorial/render_library.py"
VOLUMES = ("XF-000", "XV-001", "XEP-0000")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class ConversionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("pandoc") or not shutil.which("libreoffice"):
            raise unittest.SkipTest("Pandoc y LibreOffice son necesarios para integración")
        cls.temp = tempfile.TemporaryDirectory(prefix="xientia-integration-")
        cls.root = Path(cls.temp.name)
        cls.repo = cls.root / "repo"
        cls.repo.mkdir()
        for vol in VOLUMES:
            shutil.copytree(ROOT / "docs" / vol, cls.repo / "docs" / vol)
        shutil.copytree(ROOT / "tools/editorial", cls.repo / "tools/editorial",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        subprocess.run(["git", "init", "-q", str(cls.repo)], check=True)
        subprocess.run(["git", "-C", str(cls.repo), "add", "docs", "tools"], check=True)
        subprocess.run(["git", "-C", str(cls.repo), "-c", "user.name=Test",
                        "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], check=True)
        cls.source_hashes = {
            str(p.relative_to(cls.repo)): sha(p)
            for p in (cls.repo / "docs").rglob("*") if p.is_file()
        }

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def render(self, vol, fmt="all"):
        out = self.root / f"out-{vol}-{fmt}"
        proc = subprocess.run([sys.executable, str(self.repo / "tools/editorial/render_library.py"),
                               "--repo", str(self.repo), "--volume", vol,
                               "--out", str(out), "--format", fmt],
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return out

    def test_real_odt_pdf_for_all_volumes(self):
        for vol in VOLUMES:
            with self.subTest(volume=vol):
                out = self.render(vol)
                md = out / f"{vol}_consulta.md"
                odt = out / f"{vol}_consulta.odt"
                pdf = out / "pdf" / f"{vol}_consulta.pdf"
                manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["output_sha256"], sha(md))
                self.assertEqual(manifest["status"], "draft")
                self.assertIn("NO ADOPTADA", md.read_text(encoding="utf-8"))
                self.assertGreater(odt.stat().st_size, 1000)
                with zipfile.ZipFile(odt) as z:
                    self.assertIsNone(z.testzip())
                    self.assertIn("content.xml", z.namelist())
                    self.assertIn("styles.xml", z.namelist())
                self.assertGreater(pdf.stat().st_size, 1000)
                self.assertTrue(pdf.read_bytes().startswith(b"%PDF-"))
                self.assertFalse((out / "lo-profile").exists())
                self.assertEqual(self.source_hashes, {
                    str(p.relative_to(self.repo)): sha(p)
                    for p in (self.repo / "docs").rglob("*") if p.is_file()
                })

    def test_odt_only_does_not_create_pdf(self):
        out = self.render("XF-000", "odt")
        self.assertTrue((out / "XF-000_consulta.odt").is_file())
        self.assertFalse((out / "pdf" / "XF-000_consulta.pdf").exists())

    def test_failure_of_libreoffice_cleans_temporary_profile(self):
        spec = importlib.util.spec_from_file_location("xientia_render_integration", RENDER)
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        out = self.root / "failure-output"
        real_run = renderer.run
        profiles = []
        def intercepted(args):
            if args[0] == "libreoffice":
                profile_arg = next(a for a in args if a.startswith("-env:UserInstallation="))
                from urllib.parse import urlparse, unquote
                profiles.append(Path(unquote(urlparse(profile_arg.split("=", 1)[1]).path)))
                self.assertTrue(profiles[-1].is_dir())
                raise RuntimeError("Fallo simulado de LibreOffice")
            return real_run(args)
        argv = ["render_library.py", "--repo", str(self.repo),
                "--volume", "XF-000", "--out", str(out)]
        with patch.object(sys, "argv", argv), patch.object(renderer, "run", side_effect=intercepted):
            with self.assertRaisesRegex(RuntimeError, "Fallo simulado"):
                renderer.main()
        self.assertEqual(len(profiles), 1)
        self.assertFalse(profiles[0].exists())
        self.assertFalse((out / "lo-profile").exists())

if __name__ == "__main__":
    unittest.main()
