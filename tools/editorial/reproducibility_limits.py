"""Resource limits for the F4.4-R1 reproducibility comparator."""

MIB = 1024 * 1024

MAX_ODT_BYTES = 25 * MIB
MAX_ZIP_MEMBERS = 256
MAX_ZIP_MEMBER_BYTES = 16 * MIB
MAX_ZIP_TOTAL_BYTES = 64 * MIB

MAX_PDF_BYTES = 50 * MIB
MAX_PDF_PAGES = 500
MAX_PAGE_PIXELS = 10_000_000


def validate_file_size(path, maximum, label):
    """Reject an oversized input before processing."""
    size = path.stat().st_size

    if size > maximum:
        raise ValueError(
            f"{label} exceeds resource limit: {size} > {maximum}"
        )

    return size


def validate_zip_inventory(archive):
    """Check declared ZIP entry sizes before decompression."""
    members = archive.infolist()

    if len(members) > MAX_ZIP_MEMBERS:
        raise ValueError("ZIP member count exceeds resource limit")

    total = 0

    for member in members:
        if member.file_size > MAX_ZIP_MEMBER_BYTES:
            raise ValueError(
                "ZIP member exceeds resource limit"
            )

        total += member.file_size

        if total > MAX_ZIP_TOTAL_BYTES:
            raise ValueError(
                "ZIP total exceeds resource limit"
            )

    return {
        "members": len(members),
        "uncompressed_bytes": total,
    }


def read_zip_member_bounded(archive, member):
    """Read a ZIP member without exceeding its configured byte limit."""
    info = archive.getinfo(member)

    if info.file_size > MAX_ZIP_MEMBER_BYTES:
        raise ValueError("ZIP member exceeds resource limit")

    with archive.open(info) as stream:
        data = stream.read(MAX_ZIP_MEMBER_BYTES + 1)

        if len(data) > MAX_ZIP_MEMBER_BYTES:
            raise ValueError("ZIP actual size exceeds resource limit")

        if stream.read(1):
            raise ValueError("ZIP actual size exceeds resource limit")

    if len(data) != info.file_size:
        raise ValueError("ZIP declared and actual sizes differ")

    return data


def validate_pdf_input(path, document):
    """Validate PDF file size and page count."""
    validate_file_size(
        path, MAX_PDF_BYTES, "PDF"
    )

    if len(document) > MAX_PDF_PAGES:
        raise ValueError(
            "PDF page count exceeds resource limit"
        )


def validate_page_pixels(page):
    """Validate page dimensions at 72 DPI before rendering."""
    from math import ceil, isfinite

    width = page.rect.width
    height = page.rect.height

    if (
        not isfinite(width)
        or not isfinite(height)
        or width <= 0
        or height <= 0
        or ceil(width) * ceil(height) > MAX_PAGE_PIXELS
    ):
        raise ValueError(
            "PDF page dimensions exceed resource limit"
        )
