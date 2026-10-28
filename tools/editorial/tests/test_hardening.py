import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from validated_publish import publish_validated, sha256_file, run_supervised

class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.repo=self.root/'repo';self.repo.mkdir()
        self.out=self.root/'published'
        self.args=SimpleNamespace(repo=self.repo,out=self.out,volume='XV-001',format='all',allow_dirty=True)

    def render(self,cmd):
        stage=Path(cmd[cmd.index('--out')+1]);(stage/'pdf').mkdir(parents=True)
        (stage/'XV-001_consulta.md').write_bytes(b'markdown')
        (stage/'XV-001_consulta.odt').write_bytes(b'odt')
        (stage/'pdf/XV-001_consulta.pdf').write_bytes(b'pdf')
        (stage/'manifest.json').write_text(json.dumps(dict(document='XV-001',status='draft',edition='consulta-no-adoptada',git_commit='abc',dirty_tracked=True,output_sha256=hashlib.sha256(b'markdown').hexdigest())))

    def test_bad_markdown_hash_never_published(self):
        def bad(cmd):
            self.render(cmd)
            stage=Path(cmd[cmd.index('--out')+1]);(stage/'XV-001_consulta.md').write_bytes(b'altered')
        with patch('validated_publish.run_supervised',side_effect=bad),patch('validated_publish.git_commit',return_value='abc'):
            with self.assertRaisesRegex(ValueError,'SHA-256'):
                publish_validated(self.args,ROOT/'render_library.py')
        self.assertFalse(self.out.exists())

    def test_wrong_git_commit_never_published(self):
        with patch('validated_publish.run_supervised',side_effect=self.render),patch('validated_publish.git_commit',return_value='different'):
            with self.assertRaisesRegex(ValueError,'Commit'):
                publish_validated(self.args,ROOT/'render_library.py')
        self.assertFalse(self.out.exists())

    def test_artifact_mutation_during_validation(self):
        def mutate(volume,odt):
            odt.write_bytes(b'tampered')
            return {'chapters':15,'articles':0,'headings':142}
        with patch('validated_publish.run_supervised',side_effect=self.render),patch('validated_publish.git_commit',return_value='abc'),patch('validated_publish.validate_odt',side_effect=mutate),patch('validated_publish.validate_odt_pdf',return_value={'headings':142,'pages':52}):
            with self.assertRaisesRegex(ValueError,'alterado'):
                publish_validated(self.args,ROOT/'render_library.py')
        self.assertFalse(self.out.exists())

    def test_concurrent_destination_creation_not_overwritten(self):
        def race(volume,odt):
            self.out.mkdir();(self.out/'sentinel').write_text('preserve')
            return {'chapters':15,'articles':0,'headings':142}
        with patch('validated_publish.run_supervised',side_effect=self.render),patch('validated_publish.git_commit',return_value='abc'),patch('validated_publish.validate_odt',side_effect=race),patch('validated_publish.validate_odt_pdf',return_value={'headings':142,'pages':52}):
            with self.assertRaises(OSError):
                publish_validated(self.args,ROOT/'render_library.py')
        self.assertEqual((self.out/'sentinel').read_text(),'preserve')

    def test_renderer_failure_leaves_no_publication(self):
        def fail(cmd):
            stage=Path(cmd[cmd.index('--out')+1]);stage.mkdir()
            raise RuntimeError('conversion failed')
        with patch('validated_publish.run_supervised',side_effect=fail):
            with self.assertRaises(RuntimeError):publish_validated(self.args,ROOT/'render_library.py')
        self.assertFalse(self.out.exists())
        self.assertFalse(list(self.root.glob('.xientia-f42-*')))

if __name__=='__main__':unittest.main()
