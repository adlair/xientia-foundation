"""F4.4-R1 resource policy tests."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

EDITORIAL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITORIAL))

import reproducibility_limits as limits
from reproducibility_compare import odt_component_comparison


class ResourceLimitTests(unittest.TestCase):

    def test_file_size_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.bin"
            path.write_bytes(b"123456")

            self.assertEqual(
                limits.validate_file_size(path, 6, "sample"),
                6,
            )

            with self.assertRaisesRegex(
                ValueError, "exceeds resource limit"
            ):
                limits.validate_file_size(path, 5, "sample")

    def test_zip_member_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.zip"

            with ZipFile(path, "w") as archive:
                archive.writestr("content.xml", b"123456")

            with ZipFile(path) as archive:
                with patch.object(
                    limits, "MAX_ZIP_MEMBER_BYTES", 5
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        "ZIP member exceeds resource limit",
                    ):
                        limits.validate_zip_inventory(archive)

    def test_zip_total_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.zip"

            with ZipFile(path, "w") as archive:
                archive.writestr("a.xml", b"1234")
                archive.writestr("b.xml", b"5678")

            with ZipFile(path) as archive:
                with patch.object(
                    limits, "MAX_ZIP_TOTAL_BYTES", 7
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        "ZIP total exceeds resource limit",
                    ):
                        limits.validate_zip_inventory(archive)

    def test_odt_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.odt"

            with ZipFile(path, "w") as archive:
                archive.writestr("content.xml", b"sample")

            with patch(
                "reproducibility_compare.MAX_ODT_BYTES", 1
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "ODT A exceeds resource limit",
                ):
                    odt_component_comparison(path, path)


    def test_bounded_zip_read_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.zip"

            with ZipFile(path, "w") as archive:
                archive.writestr("content.xml", b"123456")

            with ZipFile(path) as archive:
                data = limits.read_zip_member_bounded(
                    archive, "content.xml"
                )
                self.assertEqual(data, b"123456")

    def test_bounded_zip_read_rejects_oversize(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.zip"

            with ZipFile(path, "w") as archive:
                archive.writestr("content.xml", b"123456")

            with ZipFile(path) as archive:
                with patch.object(
                    limits, "MAX_ZIP_MEMBER_BYTES", 5
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        "ZIP member exceeds resource limit",
                    ):
                        limits.read_zip_member_bounded(
                            archive, "content.xml"
                        )


    def test_pdf_file_size_limit(self):
        import pymupdf
        from reproducibility_compare import pdf_page_text

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.pdf"

            with pymupdf.open() as document:
                document.new_page()
                document.save(path)

            with patch(
                "reproducibility_compare.MAX_PDF_BYTES", 1
            ):
                with self.assertRaisesRegex(
                    ValueError, "PDF exceeds resource limit"
                ):
                    pdf_page_text(path)

    def test_pdf_page_count_limit(self):
        import pymupdf
        from reproducibility_compare import pdf_page_text

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.pdf"

            with pymupdf.open() as document:
                document.new_page()
                document.new_page()
                document.save(path)

            with patch.object(
                limits, "MAX_PDF_PAGES", 1
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "PDF page count exceeds resource limit",
                ):
                    pdf_page_text(path)

    def test_pdf_page_dimensions_limit(self):
        import pymupdf
        from reproducibility_compare import pdf_visual_comparison

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.pdf"

            with pymupdf.open() as document:
                document.new_page(width=612, height=792)
                document.save(path)

            with patch.object(
                limits, "MAX_PAGE_PIXELS", 100
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "PDF page dimensions exceed resource limit",
                ):
                    pdf_visual_comparison(path, path)


if __name__ == "__main__":
    unittest.main()
