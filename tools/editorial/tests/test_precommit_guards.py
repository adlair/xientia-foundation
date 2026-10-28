import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

atomic = load('atomic_publish', ROOT / 'atomic_publish.py')
validator = load('validator_precommit', ROOT / 'uno' / 'validate_uno_r2.py')

class PrecommitGuards(unittest.TestCase):
    def test_publish_new_directory(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d)/'src'; src.mkdir(); (src/'ok').write_text('ok')
            dst = Path(d)/'dst'
            atomic.publish_noreplace(src, dst)
            self.assertFalse(src.exists())
            self.assertEqual((dst/'ok').read_text(), 'ok')

    def test_existing_directory_never_replaced(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d)/'src'; src.mkdir()
            dst = Path(d)/'dst'; dst.mkdir(); (dst/'protected').write_text('safe')
            with self.assertRaises(FileExistsError):
                atomic.publish_noreplace(src, dst)
            self.assertTrue(src.exists())
            self.assertEqual((dst/'protected').read_text(), 'safe')

    def test_expected_commit_checked(self):
        base=['Constitución de Xientia','XF-000 · Edición de consulta — NO ADOPTADA',
              'Versión general: 0.1.0 · Estado: draft · Commit: abcdef012345','texto normativo']
        ref=base.copy();ref[2]=ref[2].replace('abcdef012345','123456789abc')
        validator.compare_document_content({'content':base},{'content':ref},'abcdef0123456789')
        with self.assertRaises(ValueError):
            validator.compare_document_content({'content':base},{'content':ref},'000000000000')
        corrupted=base.copy();corrupted[3]='texto alterado'
        with self.assertRaises(ValueError):
            validator.compare_document_content({'content':corrupted},{'content':ref},'abcdef0123456789')

if __name__=='__main__':unittest.main()
