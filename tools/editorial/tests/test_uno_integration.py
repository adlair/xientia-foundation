import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class IntegrationTests(unittest.TestCase):
    def test_syntax(self):
        for p in [ROOT/'render_library.py',ROOT/'uno_integration.py',ROOT/'normalize_editorial_odt.py']:
            ast.parse(p.read_text())
    def test_flag_is_opt_in(self):
        source=(ROOT/'render_library.py').read_text()
        self.assertIn("if args.update_index_uno:",source)
        self.assertIn("ap.add_argument('--uno-reference'",source)
    def test_existing_default_renderer_path_retained(self):
        source=(ROOT/'render_library.py').read_text()
        self.assertIn("module.style_odt(odt)",source)
        self.assertIn("extra_page_headings(odt,args.volume)",source)
    def test_no_implicit_reference(self):
        source=(ROOT/'uno_integration.py').read_text()
        self.assertIn('resolve_template(renderer.parent, args.uno_reference)',source)
