"""F4.4-R1: reproducibility comparator regression tests."""

import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

EDITORIAL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITORIAL))

from reproducibility_compare import odt_component_comparison


META_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
 xmlns:dc="http://purl.org/dc/elements/1.1/">
 <office:meta>
  <meta:creation-date>{date}</meta:creation-date>
  <dc:date>{date}</dc:date>
  <dc:title>{title}</dc:title>
 </office:meta>
</office:document-meta>
"""


class OdtComparisonTests(unittest.TestCase):

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def make_odt(
        self,
        name,
        *,
        date="2026-01-01T00:00:00Z",
        title="Xientia",
        content=b"<content/>",
        compression=ZIP_DEFLATED,
        comment=b"",
        duplicate=False,
    ):
        path = self.root / name

        with ZipFile(path, "w") as archive:
            archive.writestr(
                "content.xml",
                content,
                compress_type=compression,
            )
            archive.writestr(
                "styles.xml",
                b"<styles/>",
                compress_type=ZIP_DEFLATED,
            )
            archive.writestr(
                "meta.xml",
                META_TEMPLATE.format(
                    date=date,
                    title=title,
                ).encode("utf-8"),
                compress_type=ZIP_DEFLATED,
            )

            archive.comment = comment

            if duplicate:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr(
                        "content.xml",
                        content,
                    )

        return path

    def test_identical_components(self):
        a = self.make_odt("a.odt")
        b = self.make_odt("b.odt")

        self.assertTrue(
            odt_component_comparison(a, b)["passed"]
        )

    def test_volatile_dates_allowed(self):
        a = self.make_odt(
            "a.odt", date="2026-01-01T00:00:00Z"
        )
        b = self.make_odt(
            "b.odt", date="2026-02-01T00:00:00Z"
        )

        self.assertTrue(
            odt_component_comparison(a, b)["passed"]
        )

    def test_content_mutation_detected(self):
        a = self.make_odt("a.odt")
        b = self.make_odt(
            "b.odt", content=b"<content>changed</content>"
        )

        result = odt_component_comparison(a, b)

        self.assertFalse(result["passed"])
        self.assertIn(
            "content.xml", result["different_members"]
        )

    def test_nonvolatile_metadata_detected(self):
        a = self.make_odt("a.odt")
        b = self.make_odt(
            "b.odt", title="Modified title"
        )

        result = odt_component_comparison(a, b)

        self.assertFalse(result["passed"])
        self.assertIn(
            "meta.xml", result["different_members"]
        )

    def test_compression_difference_detected(self):
        a = self.make_odt("a.odt")
        b = self.make_odt(
            "b.odt", compression=ZIP_STORED
        )

        result = odt_component_comparison(a, b)

        self.assertFalse(result["passed"])
        self.assertTrue(
            any(
                item["member"] == "content.xml"
                and "compress_type" in item["attributes"]
                for item in result["zip_metadata_differences"]
            )
        )

    def test_archive_comment_detected(self):
        a = self.make_odt("a.odt")
        b = self.make_odt(
            "b.odt", comment=b"modified"
        )

        result = odt_component_comparison(a, b)

        self.assertFalse(result["passed"])
        self.assertIn(
            {
                "member": "<archive>",
                "attributes": ["comment"],
            },
            result["zip_metadata_differences"],
        )

    def test_duplicate_member_rejected(self):
        a = self.make_odt("a.odt")
        b = self.make_odt(
            "b.odt", duplicate=True
        )

        with self.assertRaisesRegex(
            ValueError, "Duplicate ODT entries"
        ):
            odt_component_comparison(a, b)


if __name__ == "__main__":
    unittest.main()


class IntegrityRecheckTests(unittest.TestCase):

    def test_manifest_change_detected(self):
        self.assert_recheck_detects("manifest")

    def test_evidence_change_detected(self):
        self.assert_recheck_detects("evidence")

    def assert_recheck_detects(self, kind):
        from unittest.mock import patch
        import reproducibility_compare as module

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            paths = {
                name: root / f"{name}.dat"
                for name in (
                    "markdown", "odt", "pdf",
                    "manifest", "evidence"
                )
            }

            for path in paths.values():
                path.write_bytes(b"original")

            def package():
                return {
                    "root": root,
                    "evidence": {
                        "artifacts": {
                            name: {"path": f"{name}.dat"}
                            for name in ("markdown", "odt", "pdf")
                        }
                    },
                    "verification": {
                        "document": "XV-001",
                        "git_commit": "a" * 40,
                    },
                }

            original_pdf = module.pdf_page_text

            def mutate_after_verification(_):
                paths[kind].write_bytes(b"modified")
                return ["same text"]

            with patch.object(
                module,
                "load_verified_package",
                return_value=package(),
            ), patch.object(
                module,
                "pdf_page_text",
                side_effect=mutate_after_verification,
            ), patch.object(
                module,
                "odt_component_comparison",
                return_value={
                    "passed": True,
                    "different_members": [],
                    "zip_metadata_differences": [],
                    "zip_order_identical": True,
                },
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    f"Artifact changed during comparison: {kind}",
                ):
                    module.compare_packages(
                        root, root, root
                    )


class IntegrityRecheckTests(unittest.TestCase):

    def test_manifest_mutation_detected(self):
        self._check_mutation("manifest")

    def test_evidence_mutation_detected(self):
        self._check_mutation("evidence")

    def _check_mutation(self, target):
        from unittest.mock import patch
        import reproducibility_compare as module

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packages = []

            for name in ("a", "b"):
                package = root / name
                package.mkdir()

                for filename in (
                    "document.md",
                    "document.odt",
                    "document.pdf",
                    "manifest.json",
                    "evidence.json",
                ):
                    (package / filename).write_bytes(
                        filename.encode("utf-8")
                    )

                packages.append(package)

            def fake_load(repo, package):
                package = Path(package)

                return {
                    "root": package,
                    "verification": {
                        "document": "XV-001",
                        "git_commit": "a" * 40,
                    },
                    "evidence": {
                        "artifacts": {
                            "markdown": {"path": "document.md"},
                            "odt": {"path": "document.odt"},
                            "pdf": {"path": "document.pdf"},
                        },
                    },
                }

            def mutate(*args):
                path = packages[0] / f"{target}.json"
                path.write_bytes(b"changed")
                return {"passed": True}

            with patch.object(
                module,
                "load_verified_package",
                side_effect=fake_load,
            ), patch.object(
                module,
                "pdf_page_text",
                return_value=["same text"],
            ), patch.object(
                module,
                "odt_component_comparison",
                side_effect=mutate,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    f"Artifact changed during comparison: {target}",
                ):
                    module.compare_packages(
                        root, packages[0], packages[1]
                    )
