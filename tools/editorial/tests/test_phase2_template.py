import hashlib
import json
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

EDITORIAL = Path(__file__).resolve().parents[1]
T = '{urn:oasis:names:tc:opendocument:xmlns:text:1.0}'
O = '{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'

class Phase2TemplateTests(unittest.TestCase):
    def test_sha256_and_profile(self):
        folder = EDITORIAL / 'templates/XF-000'
        config = json.loads((folder/'template.json').read_text())
        self.assertEqual(config['volume'], 'XF-000')
        self.assertEqual(config['reference_file'], 'reference.odt')
        self.assertEqual(hashlib.sha256((folder/'reference.odt').read_bytes()).hexdigest(),config['sha256'])

    def test_no_constitutional_body(self):
        with ZipFile(EDITORIAL/'templates/XF-000/reference.odt') as z:
            root = ET.fromstring(z.read('content.xml'))
        body = root.find(f'{O}body/{O}text')
        self.assertEqual(len(body.findall('.//'+T+'table-of-content')), 1)
        self.assertEqual(len(body.findall('.//'+T+'h')), 0)
        content=''.join(body.itertext())
        for forbidden in ('Artículo 1.', 'Capítulo I — La ciencia', 'Declaración Fundacional'):
            self.assertNotIn(forbidden,content)

    def test_normalized_is_integrity_reference(self):
        source = (EDITORIAL/'uno_integration.py').read_text()
        self.assertIn("'--reference', str(normalized)", source)
        r4 = (EDITORIAL/'uno/update_toc_uno_r4.py').read_text()
        self.assertIn('validate(stage / NAMES[0], stage / NAMES[1], source, args.expected_commit)', r4)

if __name__=='__main__': unittest.main()
