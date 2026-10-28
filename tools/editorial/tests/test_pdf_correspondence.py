import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from odt_structure import headings_from_odt
from pdf_correspondence import pdf_pages, validate_odt_pdf, validate_pdf_text

FIX=Path(__file__).resolve().parent/'fixtures'

class PDFCorrespondenceTests(unittest.TestCase):
    def test_real_xv(self):
        result=validate_odt_pdf('XV-001',FIX/'XV-001_consulta.odt',FIX/'XV-001_consulta.pdf')
        self.assertEqual(result['chapters'],15)

    def test_real_xep(self):
        result=validate_odt_pdf('XEP-0000',FIX/'XEP-0000_consulta.odt',FIX/'XEP-0000_consulta.pdf')
        self.assertEqual((result['chapters'],result['articles']),(11,33))

    def test_missing_heading(self):
        headings=headings_from_odt(FIX/'XV-001_consulta.odt')
        pages=pdf_pages(FIX/'XV-001_consulta.pdf')
        pages=[page.replace('Capítulo XV — Conclusión','CAPÍTULO ELIMINADO') for page in pages]
        with self.assertRaisesRegex(ValueError,'ausente'):
            validate_pdf_text('XV-001',headings,pages)

    def test_duplicate_numbered_heading(self):
        headings=headings_from_odt(FIX/'XEP-0000_consulta.odt')
        pages=pdf_pages(FIX/'XEP-0000_consulta.pdf')
        pages.append('\nCapítulo XI — Evolución de XEP-0000\n')
        with self.assertRaisesRegex(ValueError,'duplicado'):
            validate_pdf_text('XEP-0000',headings,pages)

    def test_wrong_order(self):
        headings=headings_from_odt(FIX/'XV-001_consulta.odt')
        pages=pdf_pages(FIX/'XV-001_consulta.pdf')
        text='\n'.join(pages)
        a='Capítulo I — El problema';b='Capítulo II — La oportunidad histórica'
        text=text.replace(a,'__SWAP__').replace(b,a).replace('__SWAP__',b)
        with self.assertRaisesRegex(ValueError,'fuera de orden'):
            validate_pdf_text('XV-001',headings,[text])

    def test_empty_pdf_text(self):
        headings=headings_from_odt(FIX/'XV-001_consulta.odt')
        with self.assertRaisesRegex(ValueError,'vacío'):
            validate_pdf_text('XV-001',headings,[''])

if __name__=='__main__':unittest.main()
