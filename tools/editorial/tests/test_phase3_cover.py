import hashlib
import json
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

EDITORIAL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITORIAL))
from normalize_editorial_odt import read, body, paragraphs, q, value

class Phase3Tests(unittest.TestCase):
    def setUp(self):
        self.folder = EDITORIAL / "templates/XF-000"
        self.template = self.folder / "reference.odt"

    def test_template_integrity(self):
        metadata=json.loads((self.folder/"template.json").read_text())
        self.assertEqual(hashlib.sha256(self.template.read_bytes()).hexdigest(), metadata["sha256"])
        self.assertFalse(metadata["contains_historical_text"])

    def test_dynamic_cover_markers(self):
        _, parts=read(self.template)
        b=body(parts["content.xml"])
        cover=next(e for e in b if e.tag==q("t","section") and e.get(q("t","name"))=="XientiaCover")
        texts=[value(e) for e in paragraphs([cover])]
        self.assertEqual(texts, [
            "XIENTIA / BIBLIOTECA FUNDACIONAL",
            "{{XIENTIA_TITLE}}", "{{XIENTIA_EDITION}}",
            "{{XIENTIA_METADATA}}", "{{XIENTIA_DISCLAIMER}}"
        ])
        self.assertNotIn("Commit: ", " ".join(texts))
        self.assertNotIn("Estado: draft", " ".join(texts))

    def test_no_normative_body(self):
        _, parts=read(self.template)
        b=body(parts["content.xml"])
        text=" ".join(b.itertext())
        self.assertNotIn("Artículo 1.",text)
        self.assertNotIn("Declaración Fundacional",text)

if __name__=="__main__":
    unittest.main()
