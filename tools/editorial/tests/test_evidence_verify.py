"""F4.3 R2-B1: self-contained real-artifact verification tests."""

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

sys.path.insert(0, str(EDITORIAL))
sys.path.insert(0, str(CI))

from evidence_verify import sha256_file, verify_package, verify_source_contract
from odt_structure import validate_odt
from pdf_correspondence import validate_odt_pdf


class EvidenceVerifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(
            prefix="xientia-f43-r2b-tests-"
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

        import pymupdf

        cls.tools = {
            "python": sys.version.split()[0],
            "libreoffice": subprocess.check_output(
                ["libreoffice", "--version"], text=True
            ).strip(),
            "pandoc": subprocess.check_output(
                ["pandoc", "--version"], text=True
            ).splitlines()[0],
            "pymupdf": pymupdf.VersionBind,
        }

    def make_evidence(self, volume, root):
        paths = {
            "markdown": f"{volume}_consulta.md",
            "odt": f"{volume}_consulta.odt",
            "pdf": f"pdf/{volume}_consulta.pdf",
        }

        structure = validate_odt(volume, root / paths["odt"])
        correspondence = validate_odt_pdf(
            volume,
            root / paths["odt"],
            root / paths["pdf"],
        )

        return {
            "schema_version": "1.0.0",
            "phase": "F4.3-R2",
            "document": volume,
            "status": "draft",
            "edition": "consulta-no-adoptada",
            "institutional_adoption": False,
            "provenance": {
                "git_commit": self.commit,
                "dirty_tracked": False,
            },
            "artifacts": {
                kind: {
                    "path": relative,
                    "sha256": sha256_file(root / relative),
                }
                for kind, relative in paths.items()
            },
            "tools": self.tools,
            "validation": {
                "odt_structure": {
                    "passed": True,
                    "details": structure,
                },
                "pdf_correspondence": {
                    "passed": True,
                    "details": correspondence,
                },
            },
        }

    def test_real_packages(self):
        for volume, root in self.packages.items():
            with self.subTest(volume=volume):
                evidence = self.make_evidence(volume, root)
                result = verify_package(self.repo, root, evidence)
                self.assertEqual(result["artifacts_verified"], 3)

    def test_wrong_commit_rejected(self):
        root = self.packages["XV-001"]
        evidence = self.make_evidence("XV-001", root)
        evidence["provenance"]["git_commit"] = "f" * 40

        with self.assertRaises(ValueError):
            verify_package(self.repo, root, evidence)

    def test_wrong_markdown_hash_rejected(self):
        root = self.packages["XV-001"]
        evidence = self.make_evidence("XV-001", root)
        evidence["artifacts"]["markdown"]["sha256"] = "0" * 64

        with self.assertRaises(ValueError):
            verify_package(self.repo, root, evidence)

    def test_wrong_pdf_hash_rejected(self):
        root = self.packages["XEP-0000"]
        evidence = self.make_evidence("XEP-0000", root)
        evidence["artifacts"]["pdf"]["sha256"] = "0" * 64

        with self.assertRaises(ValueError):
            verify_package(self.repo, root, evidence)

    def test_falsified_structure_rejected(self):
        root = self.packages["XV-001"]
        evidence = self.make_evidence("XV-001", root)
        evidence["validation"]["odt_structure"]["details"][
            "chapters"
        ] = 999

        with self.assertRaises(ValueError):
            verify_package(self.repo, root, evidence)

    def test_falsified_pdf_validation_rejected(self):
        root = self.packages["XEP-0000"]
        evidence = self.make_evidence("XEP-0000", root)
        evidence["validation"]["pdf_correspondence"]["details"][
            "pages"
        ] = 999

        with self.assertRaises(ValueError):
            verify_package(self.repo, root, evidence)

    def test_physical_markdown_mutation_rejected(self):
        volume = "XV-001"
        original = self.packages[volume]

        with tempfile.TemporaryDirectory(
            prefix="xientia-mutated-md-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(original, root)

            evidence = self.make_evidence(volume, root)
            markdown = root / f"{volume}_consulta.md"

            with markdown.open("a", encoding="utf-8") as stream:
                stream.write("\nALTERACION EXPERIMENTAL\n")

            with self.assertRaises(ValueError):
                verify_package(self.repo, root, evidence)

    def test_physical_pdf_mutation_rejected(self):
        volume = "XEP-0000"
        original = self.packages[volume]

        with tempfile.TemporaryDirectory(
            prefix="xientia-mutated-pdf-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(original, root)

            evidence = self.make_evidence(volume, root)
            pdf = root / "pdf" / f"{volume}_consulta.pdf"

            with pdf.open("ab") as stream:
                stream.write(b"\nEXPERIMENTAL-MUTATION\n")

            with self.assertRaises(ValueError):
                verify_package(self.repo, root, evidence)


    def test_symlink_pdf_directory_rejected(self):
        volume = "XV-001"
        original = self.packages[volume]

        with tempfile.TemporaryDirectory(
            prefix="xientia-symlink-pdf-"
        ) as temporary:
            base = Path(temporary)
            root = base / "package"
            shutil.copytree(original, root)

            evidence = self.make_evidence(volume, root)

            pdf_directory = root / "pdf"
            external = base / "external-pdf"

            pdf_directory.rename(external)
            pdf_directory.symlink_to(
                external,
                target_is_directory=True,
            )

            with self.assertRaisesRegex(
                ValueError, "Symlink artifact"
            ):
                verify_package(self.repo, root, evidence)


    def assert_manifest_rejected(self, mutate, message):
        volume = "XV-001"

        with tempfile.TemporaryDirectory(
            prefix="xientia-manifest-negative-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(self.packages[volume], root)

            evidence = self.make_evidence(volume, root)
            manifest_path = root / "manifest.json"

            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )

            mutate(manifest)

            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, message):
                verify_package(self.repo, root, evidence)

    def test_missing_source_rejected(self):
        def mutate(manifest):
            first = next(iter(manifest["sources"]))
            del manifest["sources"][first]

        self.assert_manifest_rejected(
            mutate, "Editorial source set mismatch"
        )

    def test_extra_source_rejected(self):
        def mutate(manifest):
            manifest["sources"]["docs/extra.md"] = "a" * 64

        self.assert_manifest_rejected(
            mutate, "Editorial source set mismatch"
        )

    def test_wrong_source_order_rejected(self):
        def mutate(manifest):
            items = list(manifest["sources"].items())
            items[0], items[1] = items[1], items[0]
            manifest["sources"] = dict(items)

        self.assert_manifest_rejected(
            mutate, "Editorial source set mismatch"
        )

    def test_wrong_validation_rule_rejected(self):
        def mutate(manifest):
            manifest["validation"]["last"] = 999

        self.assert_manifest_rejected(
            mutate, "Editorial validation rule mismatch"
        )

    def test_wrong_committed_source_hash_rejected(self):
        def mutate(manifest):
            first = next(iter(manifest["sources"]))
            manifest["sources"][first] = "f" * 64

        self.assert_manifest_rejected(
            mutate, "Git committed source mismatch"
        )


    def test_modified_editorial_profile_rejected(self):
        volume = "XV-001"
        root = self.packages[volume]
        evidence = self.make_evidence(volume, root)

        with tempfile.TemporaryDirectory(
            prefix="xientia-profile-mutation-"
        ) as temporary:
            repo = Path(temporary) / "repo"

            subprocess.run(
                [
                    "git", "clone", "--no-hardlinks",
                    "--quiet", str(self.repo), str(repo),
                ],
                check=True,
            )

            profile = repo / "tools/editorial/config/XV-001.json"

            data = json.loads(
                profile.read_text(encoding="utf-8")
            )
            data["validation"]["last"] = 999

            profile.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "Dirty repository rejected|Editorial profile Git mismatch",
            ):
                verify_package(repo, root, evidence)


    def test_profile_git_bytes_mismatch_rejected(self):
        volume = "XV-001"
        root = self.packages[volume]

        manifest = json.loads(
            (root / "manifest.json").read_text(encoding="utf-8")
        )

        with tempfile.TemporaryDirectory(
            prefix="xientia-profile-git-bytes-"
        ) as temporary:
            repo = Path(temporary) / "repo"

            subprocess.run(
                [
                    "git", "clone", "--no-hardlinks",
                    "--quiet", str(self.repo), str(repo),
                ],
                check=True,
            )

            profile = repo / "tools/editorial/config/XV-001.json"

            data = json.loads(
                profile.read_text(encoding="utf-8")
            )

            data["validation"]["last"] = 999

            profile.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "Editorial profile Git mismatch",
            ):
                verify_source_contract(
                    repo,
                    volume,
                    manifest,
                    self.commit,
                )


    def test_manifest_mutation_during_validation_rejected(self):
        volume = "XV-001"

        with tempfile.TemporaryDirectory(
            prefix="xientia-manifest-race-"
        ) as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(self.packages[volume], root)

            evidence = self.make_evidence(volume, root)
            manifest_path = root / "manifest.json"

            original_validate = validate_odt

            def mutate_then_validate(document, odt):
                manifest = json.loads(
                    manifest_path.read_text(encoding="utf-8")
                )

                manifest["experimental_mutation"] = True

                manifest_path.write_text(
                    json.dumps(
                        manifest,
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

                return original_validate(document, odt)

            with patch(
                "evidence_verify.validate_odt",
                side_effect=mutate_then_validate,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "Manifest changed during validation",
                ):
                    verify_package(self.repo, root, evidence)


if __name__ == "__main__":
    unittest.main()
