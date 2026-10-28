#!/usr/bin/env python3
"""Read-only validation of XF-000 UNO ODT/PDF, including link targets."""
import argparse
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

TEXT='urn:oasis:names:tc:opendocument:xmlns:text:1.0'
OFFICE='urn:oasis:names:tc:opendocument:xmlns:office:1.0'
def q(name): return '{%s}%s'%(TEXT,name)
def text(el): return ''.join(el.itertext()).strip()

def odt_info(path):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None: raise ValueError('ODT ZIP dañado')
        root=ET.fromstring(z.read('content.xml'))
    body=root.find('{%s}body/{%s}text'%(OFFICE,OFFICE))
    toc=body.find('.//'+q('table-of-content'))
    if toc is None: raise ValueError('Sin índice ODF')
    source=toc.find(q('table-of-content-source'))
    if source is None or source.get(q('outline-level'))!='1':raise ValueError('Índice no es nivel 1')
    headings=body.findall('.//'+q('h'))
    articles=[]; main=[]
    for h in headings:
        title=text(h)
        m=re.match(r'^Artículo\s+(\d+)\.',title)
        if m:
            articles.append(int(m.group(1)))
            if h.get(q('outline-level'))!='2':raise ValueError('Artículo fuera del nivel 2: '+title)
        elif h.get(q('outline-level'))=='1':main.append(title)
    toc_body=toc.find(q('index-body'))
    entries=[text(p) for p in toc_body.iter(q('p'))] if toc_body is not None else []
    # Extract the body as ordered paragraphs and headings, omitting generated TOC cache.
    content=[]
    def visit(e):
        if e is toc:return
        if e.tag in (q('p'),q('h')):
            content.append(text(e))
            return
        for child in e:visit(child)
    visit(body)
    return {'articles':articles,'main':main,'entries':entries,'content':content}

METADATA_RE = re.compile(
    r"^Versión general: (?P<version>0\.1\.0) · Estado: (?P<status>draft) · Commit: (?P<commit>[0-9a-f]{12})$"
)

def compare_document_content(actual, reference, expected_commit=None):
    """Compare all paragraphs, allowing only a legitimate metadata commit change."""
    a = list(actual['content'])
    b = list(reference['content'])
    if len(a) != len(b):
        raise ValueError('Cantidad de párrafos diferente')
    candidates = [(i, METADATA_RE.fullmatch(x), METADATA_RE.fullmatch(y))
                  for i, (x, y) in enumerate(zip(a, b))
                  if x.startswith('Versión general:') or y.startswith('Versión general:')]
    if len(candidates) != 1 or not candidates[0][1] or not candidates[0][2]:
        raise ValueError('Metadatos ausentes, duplicados o inválidos')
    index, current, previous = candidates[0]
    if expected_commit is not None and current.group('commit') != expected_commit[:12]:
        raise ValueError('Commit de portada no coincide con Git')
    a[index] = b[index] = '<METADATOS DE EDICIÓN VALIDADOS>'
    if a != b:
        raise ValueError('Diferencia en contenido documental, fuera de metadatos')
    return current.group('commit')

def validate(odt,pdf,reference,expected_commit=None):
    import pymupdf as fitz
    actual=odt_info(odt)
    if not (actual['articles']==list(range(1,67))): raise ValueError('Secuencia de artículos incorrecta')
    if not (len(actual['main'])==13): raise ValueError('No hay exactamente 13 encabezados principales')
    if not (len(actual['entries'])==13): raise ValueError('No hay exactamente 13 entradas de índice')
    if not (all('Artículo ' not in e for e in actual['entries'])): raise ValueError('Índice contiene artículos')
    if reference:
        before=odt_info(reference)
        compare_document_content(actual, before, expected_commit)
    elif expected_commit is not None:
        compare_document_content(actual, actual, expected_commit)
    doc=fitz.open(pdf)
    if not (len(doc)>=3): raise ValueError('PDF demasiado corto')
    if not ('NO ADOPTADA' in doc[0].get_text()): raise ValueError('Falta advertencia de no adopción')
    page=doc[1]
    links=[x for x in page.get_links() if x.get('kind')==fitz.LINK_GOTO]
    expected=[]
    for entry in actual['entries']:
        m=re.search(r'(\d+)\s*$',entry)
        if not m:raise ValueError('Entrada sin página: '+entry)
        expected.append(int(m.group(1)))
    actual_targets={link['page']+1 for link in links if link.get('page',-1)>=0}
    if actual_targets != set(expected): raise ValueError(f'Destinos PDF {actual_targets} vs índice {set(expected)}')
    if len(links) < 13: raise ValueError('Faltan enlaces internos')
    for title, page_num in zip(actual['main'], expected):
        if not 1 <= page_num <= len(doc): raise ValueError('Página fuera de rango')
        if title not in doc[page_num-1].get_text(): raise ValueError(f'Título ausente en página {page_num}: {title}')
    pdf_text='\n'.join(p.get_text() for p in doc)
    numbers=[int(n) for n in re.findall(r'Artículo\s+(\d+)\.',pdf_text)]
    if not (numbers==list(range(1,67))): raise ValueError('Secuencia PDF de artículos incorrecta')
    print('VALIDACIÓN OK:',len(doc),'páginas;',len(actual['entries']),'entradas;',len(links),'enlaces;',len(numbers),'artículos')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--odt',type=Path,required=True)
    p.add_argument('--pdf',type=Path,required=True)
    p.add_argument('--reference',type=Path)
    a=p.parse_args()
    validate(a.odt,a.pdf,a.reference)
