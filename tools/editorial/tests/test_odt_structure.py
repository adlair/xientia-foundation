import sys
import unittest
from pathlib import Path
from dataclasses import replace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from odt_structure import headings_from_odt,validate_structure,validate_odt
FIX=Path(__file__).resolve().parent/'fixtures'

class ODTStructureTests(unittest.TestCase):
    def test_real_xv(self):
        self.assertEqual(validate_odt('XV-001',FIX/'XV-001_consulta.odt')['chapters'],15)
    def test_real_xep(self):
        result=validate_odt('XEP-0000',FIX/'XEP-0000_consulta.odt')
        self.assertEqual((result['chapters'],result['articles']),(11,33))
    def test_missing_chapter(self):
        hs=headings_from_odt(FIX/'XV-001_consulta.odt')
        hs=[h for h in hs if not h.title.startswith('Capítulo III ')]
        with self.assertRaisesRegex(ValueError,'capítulos'):validate_structure('XV-001',hs)
    def test_duplicate_article(self):
        hs=headings_from_odt(FIX/'XEP-0000_consulta.odt')
        pos=next(i for i,h in enumerate(hs) if h.title.startswith('Artículo 2.'))
        hs.insert(pos,hs[pos])
        with self.assertRaisesRegex(ValueError,'artículos'):validate_structure('XEP-0000',hs)
    def test_wrong_heading_level(self):
        hs=headings_from_odt(FIX/'XV-001_consulta.odt')
        pos=next(i for i,h in enumerate(hs) if h.title.startswith('Capítulo I '))
        hs[pos]=replace(hs[pos],level=2)
        with self.assertRaisesRegex(ValueError,'nivel'):validate_structure('XV-001',hs)
    def test_wrong_section_order(self):
        hs=headings_from_odt(FIX/'XV-001_consulta.odt')
        pos=next(i for i,h in enumerate(hs) if h.title.startswith('1.2.'))
        hs[pos]=replace(hs[pos],title='1.8. Sección alterada')
        with self.assertRaisesRegex(ValueError,'Subsecciones'):validate_structure('XV-001',hs)

if __name__=='__main__':unittest.main()
