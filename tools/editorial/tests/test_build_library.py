"""Black-box regression tests for Xientia multivolume Markdown builder.
Run: python3 -m unittest discover -s tools/editorial/tests -v
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BUILDER = ROOT / 'tools/editorial/build_library.py'
CONFIG = ROOT / 'tools/editorial/config'
VOLUMES = ('XF-000', 'XV-001', 'XEP-0000')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MultivolumeBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BUILDER.is_file():
            raise unittest.SkipTest('build_library.py no está instalado')
        cls.temp = tempfile.TemporaryDirectory(prefix='xientia-tests-')
        cls.work = Path(cls.temp.name)
        cls.repo = cls.work / 'repo'
        cls.repo.mkdir()
        # Work on a self-contained copy, never alter the user's working tree.
        for volume in VOLUMES:
            shutil.copytree(ROOT / 'docs' / volume, cls.repo / 'docs' / volume)
        subprocess.run(['git', 'init', '-q', str(cls.repo)], check=True)
        subprocess.run(['git', '-C', str(cls.repo), '-c', 'user.name=Test',
                        '-c', 'user.email=test@example.invalid', 'add', 'docs'], check=True)
        subprocess.run(['git', '-C', str(cls.repo), '-c', 'user.name=Test',
                        '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        cls.config = cls.work / 'config'
        shutil.copytree(CONFIG, cls.config)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'temp'):
            cls.temp.cleanup()

    def run_builder(self, volume, config=None, expect_success=True):
        output = self.work / ('output-' + volume)
        if output.exists():
            shutil.rmtree(output)
        cmd = [sys.executable, str(BUILDER), '--repo', str(self.repo),
               '--volume', volume, '--out', str(output),
               '--config-dir', str(config or self.config)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if expect_success:
            self.assertEqual(p.returncode, 0, p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout)
        return output, p

    def altered_config(self, volume, edit):
        config = self.work / ('bad-' + str(len(list(self.work.glob('bad-*')))))
        shutil.copytree(self.config, config)
        path = config / (volume + '.json')
        data = json.loads(path.read_text(encoding='utf-8'))
        edit(data)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        return config

    def test_all_volumes_reproducible_and_manifest(self):
        for volume in VOLUMES:
            with self.subTest(volume=volume):
                source_paths = [p for p in (self.repo / 'docs' / volume).rglob('*') if p.is_file()]
                before = {str(p): sha(p) for p in source_paths}
                out, _ = self.run_builder(volume)
                md = out / (volume + '_consulta.md')
                manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
                first = md.read_bytes()
                self.assertEqual(manifest['document'], volume)
                self.assertEqual(manifest['document_version'], '0.1.0')
                self.assertEqual(manifest['status'], 'draft')
                self.assertEqual(manifest['edition'], 'consulta-no-adoptada')
                self.assertFalse(manifest['dirty_tracked'])
                self.assertEqual(manifest['output_sha256'], sha(md))
                self.assertIn('NO ADOPTADA', md.read_text(encoding='utf-8'))
                for rel, expected in manifest['sources'].items():
                    self.assertEqual(sha(self.repo / rel), expected)
                out, _ = self.run_builder(volume)
                self.assertEqual(first, (out / (volume + '_consulta.md')).read_bytes())
                self.assertEqual(before, {str(p): sha(p) for p in source_paths})

    def test_missing_path_rejected(self):
        cfg = self.altered_config('XV-001', lambda d: d['chapter_files'].__setitem__(0, 'docs/XV-001/chapters/missing.md'))
        self.run_builder('XV-001', cfg, False)

    def test_duplicate_source_rejected(self):
        cfg = self.altered_config('XV-001', lambda d: d['prefix'].append(d['prefix'][0]))
        self.run_builder('XV-001', cfg, False)

    def test_outside_repo_rejected(self):
        cfg = self.altered_config('XV-001', lambda d: d['prefix'].__setitem__(0, '../../etc/passwd.md'))
        self.run_builder('XV-001', cfg, False)

    def test_wrong_chapter_order_rejected(self):
        cfg = self.altered_config('XEP-0000', lambda d: d['chapter_files'].reverse())
        self.run_builder('XEP-0000', cfg, False)

    def test_wrong_article_sequence_rejected(self):
        cfg = self.altered_config('XF-000', lambda d: d['chapter_1_files'].pop(0))
        self.run_builder('XF-000', cfg, False)

    def test_non_draft_metadata_rejected(self):
        path = self.repo / 'docs/XV-001/metadata.yaml'
        old = path.read_text(encoding='utf-8')
        try:
            self.assertIn('status: draft', old)
            path.write_text(old.replace('status: draft', 'status: approved'), encoding='utf-8')
            self.run_builder('XV-001', expect_success=False)
        finally:
            path.write_text(old, encoding='utf-8')

    def test_output_inside_repository_rejected(self):
        cmd = [sys.executable, str(BUILDER), '--repo', str(self.repo), '--volume', 'XV-001',
               '--out', str(self.repo / 'generated'), '--config-dir', str(self.config)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse((self.repo / 'generated').exists())


if __name__ == '__main__':
    unittest.main()
