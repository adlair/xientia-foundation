"""F4.3 R2-B2: self-contained evidence generator tests."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

EDITORIAL = Path(__file__).resolve().parents[1]
CI = EDITORIAL / "ci"
SOURCE_REPO = EDITORIAL.parents[1]

sys.path.insert(0, str(CI))

from evidence_generate import generate_evidence, write_evidence, generate_and_write_evidence
from evidence_schema import validate_evidence


class EvidenceGenerateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(
            prefix="xientia-f43-r2b2-tests-"
        )
        cls.addClassCleanup(cls.temporary.cleanup)

        cls.base = Path(cls.temporary.name)
        cls.repo = cls.base / "repo"

        subprocess.run(
            [
                "git", "clone", "--no-hardlinks",
                "--quiet", str(SOURCE_REPO), str(cls.repo),
            ],
            check=True,
        )

        cls.commit = subprocess.check_output(
            ["git", "-C", str(cls.repo), "rev-parse", "HEAD"],
            text=True,
        ).strip()

        cls.packages = {}

        for volume in ("XV-001", "XEP-0000"):
            output = cls.base / volume

            subprocess.run(
                [
                    sys.executable,
                    str(cls.repo / "tools/editorial/render_library.py"),
                    "--repo", str(cls.repo),
                    "--volume", volume,
                    "--out", str(output),
                    "--validate-publish",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )

            cls.packages[volume] = output

    def test_real_generation(self):
        for volume, root in self.packages.items():
            with self.subTest(volume=volume):
                evidence = generate_evidence(
                    self.repo, root, volume
                )

                self.assertTrue(validate_evidence(evidence))
                self.assertEqual(
                    evidence["provenance"]["git_commit"],
                    self.commit,
                )
                self.assertEqual(len(evidence["artifacts"]), 3)
                self.assertFalse(
                    (root / "evidence.json").exists()
                )

    def test_unsupported_volume_rejected(self):
        with self.assertRaisesRegex(
            ValueError, "Unsupported evidence volume"
        ):
            generate_evidence(
                self.repo,
                self.packages["XV-001"],
                "XF-000",
            )

    def test_dirty_repository_rejected(self):
        with tempfile.TemporaryDirectory(
            prefix="xientia-dirty-repo-"
        ) as temporary:
            repo = Path(temporary) / "repo"

            subprocess.run(
                [
                    "git", "clone", "--no-hardlinks",
                    "--quiet", str(self.repo), str(repo),
                ],
                check=True,
            )

            (repo / "untracked-test.txt").write_text(
                "experimental", encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ValueError, "Dirty repository rejected"
            ):
                generate_evidence(
                    repo,
                    self.packages["XV-001"],
                    "XV-001",
                )

    def test_wrong_manifest_commit_rejected(self):
        volume = "XV-001"

        with tempfile.TemporaryDirectory(
            prefix="xientia-wrong-commit-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(self.packages[volume], root)

            manifest_path = root / "manifest.json"
            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
            manifest["git_commit"] = "f" * 40

            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "Manifest Git commit mismatch"
            ):
                generate_evidence(self.repo, root, volume)

    def test_missing_artifact_rejected(self):
        volume = "XEP-0000"

        with tempfile.TemporaryDirectory(
            prefix="xientia-missing-artifact-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(self.packages[volume], root)

            pdf = root / "pdf" / f"{volume}_consulta.pdf"
            pdf.unlink()

            with self.assertRaises(FileNotFoundError):
                generate_evidence(self.repo, root, volume)


    def test_write_evidence_success(self):
        with tempfile.TemporaryDirectory(
            prefix="xientia-write-success-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(self.packages["XV-001"], root)

            evidence = generate_evidence(
                self.repo, root, "XV-001"
            )

            destination = write_evidence(root, evidence)

            self.assertEqual(
                json.loads(destination.read_text(encoding="utf-8")),
                evidence,
            )

            self.assertEqual(
                list(root.glob(".xientia-evidence-*.tmp")),
                [],
            )

    def test_existing_evidence_not_replaced(self):
        with tempfile.TemporaryDirectory(
            prefix="xientia-write-existing-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(self.packages["XV-001"], root)

            evidence = generate_evidence(
                self.repo, root, "XV-001"
            )

            destination = root / "evidence.json"
            destination.write_bytes(b"ORIGINAL")

            with self.assertRaises(FileExistsError):
                write_evidence(root, evidence)

            self.assertEqual(
                destination.read_bytes(),
                b"ORIGINAL",
            )

    def test_symlink_evidence_rejected(self):
        with tempfile.TemporaryDirectory(
            prefix="xientia-write-symlink-"
        ) as temporary:
            base = Path(temporary)
            root = base / "package"
            shutil.copytree(self.packages["XV-001"], root)

            evidence = generate_evidence(
                self.repo, root, "XV-001"
            )

            external = base / "external.json"
            external.write_bytes(b"EXTERNAL")

            (root / "evidence.json").symlink_to(external)

            with self.assertRaises(FileExistsError):
                write_evidence(root, evidence)

            self.assertEqual(
                external.read_bytes(),
                b"EXTERNAL",
            )

    def test_link_failure_cleans_temporary(self):
        with tempfile.TemporaryDirectory(
            prefix="xientia-write-failure-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(self.packages["XV-001"], root)

            evidence = generate_evidence(
                self.repo, root, "XV-001"
            )

            with patch(
                "os.link",
                side_effect=OSError("simulated link failure"),
            ):
                with self.assertRaisesRegex(
                    OSError, "simulated link failure"
                ):
                    write_evidence(root, evidence)

            self.assertFalse(
                (root / "evidence.json").exists()
            )

            self.assertEqual(
                list(root.glob(".xientia-evidence-*.tmp")),
                [],
            )


    def test_generate_and_write_integration(self):
        volume = "XEP-0000"

        with tempfile.TemporaryDirectory(
            prefix="xientia-evidence-integration-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(self.packages[volume], root)

            destination = generate_and_write_evidence(
                self.repo, root, volume
            )

            self.assertTrue(destination.is_file())

            evidence = json.loads(
                destination.read_text(encoding="utf-8")
            )

            self.assertTrue(validate_evidence(evidence))
            self.assertEqual(evidence["document"], volume)
            self.assertEqual(
                evidence["provenance"]["git_commit"],
                self.commit,
            )

            with self.assertRaises(FileExistsError):
                generate_and_write_evidence(
                    self.repo, root, volume
                )


    def test_post_publish_read_failure_preserves_destination(self):
        volume = "XV-001"

        with tempfile.TemporaryDirectory(
            prefix="xientia-post-publish-failure-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(self.packages[volume], root)

            evidence = generate_evidence(
                self.repo, root, volume
            )

            destination = root / "evidence.json"

            original_read_bytes = Path.read_bytes

            def fail_destination_read(path):
                if path == destination:
                    raise OSError("simulated post-publish read failure")
                return original_read_bytes(path)

            with patch.object(
                Path,
                "read_bytes",
                autospec=True,
                side_effect=fail_destination_read,
            ):
                with self.assertRaisesRegex(
                    OSError,
                    "simulated post-publish read failure",
                ):
                    write_evidence(root, evidence)

            self.assertTrue(destination.is_file())
            self.assertEqual(
                json.loads(destination.read_text(encoding="utf-8")),
                evidence,
            )
            self.assertEqual(
                list(root.glob(".xientia-evidence-*.tmp")),
                [],
            )


if __name__ == "__main__":
    unittest.main()
