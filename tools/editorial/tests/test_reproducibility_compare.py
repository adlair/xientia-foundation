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
