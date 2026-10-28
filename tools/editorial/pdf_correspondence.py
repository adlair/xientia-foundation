"""Experimental F4.1 R2: compare PDF text headings to validated ODT headings.

Read-only; does not change UNO or publishing. Uses PyMuPDF.
"""
import re
from pathlib import Path

from odt_structure import headings_from_odt, validate_structure


def pdf_pages(path):
    import pymupdf
    with pymupdf.open(path) as doc:
        if not doc.page_count:
            raise ValueError('PDF sin páginas')
        return [page.get_text(sort=True) for page in doc]


def _heading_line_positions(text, title):
    # Exact heading line after whitespace normalization; do not match prefixes
    # such as 'Capítulo I' inside 'Capítulo II'.
    title = ' '.join(title.split())
    lines = text.splitlines()
    positions = []
    for index, line in enumerate(lines):
        if ' '.join(line.split()) == title:
            positions.append(index)
    return positions


def validate_pdf_text(volume, headings, pages):
    """Check every ODT heading appears in PDF in the same document order.

    Also ensure unique occurrences for numbered chapter/article headings.
    The page extraction is intentionally read-only and does not infer PDF tags.
    """
    validate_structure(volume, headings)
    if not pages or not any(page.strip() for page in pages):
        raise ValueError('PDF vacío')
    # Some PDF renderers wrap long headings across lines. For the validated
    # reference fixtures, all headings are single lines; reject wrapping
    # rather than silently accepting a fuzzy match.
    ordered=[]
    for page_number, page in enumerate(pages):
        for line_number, line in enumerate(page.splitlines()):
            ordered.append((page_number, line_number, ' '.join(line.split())))
    cursor=0
    matched=[]
    for heading in headings:
        title=' '.join(heading.title.split())
        indices=[i for i,(_,_,line) in enumerate(ordered) if line==title]
        if not indices:
            raise ValueError('Encabezado ausente en PDF: '+title)
        match=next((i for i in indices if i>=cursor),None)
        if match is None:
            raise ValueError('Encabezados PDF fuera de orden: '+title)
        if re.match(r'^(?:Capítulo\s+[IVXLCDM]+\s+—|Artículo\s+\d+\.)',title) and len(indices)!=1:
            raise ValueError('Encabezado numerado duplicado en PDF: '+title)
        matched.append((title,ordered[match][0]+1))
        cursor=match+1
    return {'volume':volume,'pages':len(pages),'headings':len(matched),
            'chapters':sum(t.startswith('Capítulo ') for t,_ in matched),
            'articles':sum(t.startswith('Artículo ') for t,_ in matched)}


def validate_odt_pdf(volume, odt_path, pdf_path):
    return validate_pdf_text(volume,headings_from_odt(Path(odt_path)),pdf_pages(Path(pdf_path)))
