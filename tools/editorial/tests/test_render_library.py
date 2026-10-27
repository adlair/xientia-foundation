"""Focused renderer regression checks (stdlib only)."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "render_library.py"
spec = importlib.util.spec_from_file_location("xientia_renderer", MODULE)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)

class RenderTests(unittest.TestCase):
    def test_libreoffice_profile_is_temporary(self):
        import inspect
        source = inspect.getsource(renderer.main)
        self.assertIn("TemporaryDirectory", source)
        self.assertNotIn("out/'lo-profile'", source)

    def test_render_does_not_modify_markdown_source(self):
        # Renderer invokes the existing builder; it must not rewrite its Markdown.
        import inspect
        source = inspect.getsource(renderer.main)
        self.assertNotIn("md.write_text", source)
        self.assertNotIn("md.write_bytes", source)

    def test_document_source_reference_is_unchanged(self):
        # The BibTeX notation and link remain in the source; styling is separate.
        source = Path(__file__).resolve().parents[3] / "docs/XV-001/references.md"
        text = source.read_text(encoding="utf-8")
        self.assertIn("[@unesco2021]", text)
        self.assertIn("bibliography/references.bib", text)

if __name__ == "__main__":
    unittest.main()
