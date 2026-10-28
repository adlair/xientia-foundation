#!/usr/bin/env python3
"""XF-000 experimental ODT normalizer, based on validated editorial reference.
Does not modify source Markdown. Reference provides styling, not body text.
"""
import argparse, copy, os, re, tempfile, zipfile
from pathlib import Path
from lxml import etree as E

NS={'o':'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    't':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
def q(p,n):return '{%s}%s'%(NS[p],n)
def read(path):
    with zipfile.ZipFile(path) as z:
        if z.testzip():raise ValueError('ODT inválido')
        entries=[(i,z.read(i.filename)) for i in z.infolist()]
    return entries,{n:E.fromstring(next(d for i,d in entries if i.filename==n)) for n in ('content.xml','styles.xml')}
def body(root):
    return root.find('o:body/o:text',NS)
def paragraphs(elements):
    return [e for element in elements for e in element.iter()
            if e.tag in (q('t','p'),q('t','h'))]
def value(e):return ''.join(e.itertext())
def main(source,reference,destination):
    source,reference,destination=map(Path,(source,reference,destination))
    if source.resolve()==destination.resolve() or reference.resolve()==destination.resolve():
        raise ValueError('No sobrescribir originales')
    entries,original=read(source)
    _,ref=read(reference)
    ob=body(original['content.xml']);rb=body(ref['content.xml'])
    original_nodes=list(ob)
    toc=[x for x in original_nodes if x.tag==q('t','table-of-content')]
    if len(toc)!=1:raise ValueError('Se requiere un índice original')
    original_text=paragraphs([x for x in original_nodes if x is not toc[0]])
    if len(original_text)<100:raise ValueError('ODT inesperadamente pequeño')
    headings=[e for e in original_text if e.tag==q('t','h')]
    articles=[e for e in headings if re.match(r'^Artículo\s+\d+\.',value(e))]
    if [int(re.match(r'^Artículo\s+(\d+)',value(e)).group(1)) for e in articles]!=list(range(1,67)):
        raise ValueError('Secuencia constitucional incorrecta')
    # The four original front-matter paragraphs are moved, never rewritten.
    front=original_nodes[1:5]
    if not (front[0].tag==q('t','h') and value(front[0])=='Constitución de Xientia'
            and 'NO ADOPTADA' in value(front[1])):
        raise ValueError('Portadilla original no reconocida')
    # Take reference editorial styles, cover and index scaffolding, not normative content.
    ref_nodes=list(rb)
    cover=next((x for x in ref_nodes if x.tag==q('t','section')
                and x.get(q('t','name'))=='XientiaCover'),None)
    index_label=next((x for x in ref_nodes if x.tag==q('t','p') and value(x)=='Índice'),None)
    ref_toc=next((x for x in ref_nodes if x.tag==q('t','table-of-content')),None)
    if cover is None or index_label is None or ref_toc is None:
        raise ValueError('Referencia sin portada o índice validado')
    # The reference supplies styles, never edition-specific metadata.
    # Preserve the exact four current front-matter strings in the cover.
    cover_paragraphs=paragraphs([cover])
    if len(cover_paragraphs)!=5 or value(cover_paragraphs[0])!='XIENTIA / BIBLIOTECA FUNDACIONAL':
        raise ValueError('Estructura de portada de referencia inesperada')
    if value(front[1])!='XF-000 · Edición de consulta — NO ADOPTADA':
        raise ValueError('Identificador o condición institucional inesperados')
    metadata=value(front[2])
    if not re.fullmatch(r'Versión general: 0\.1\.0 · Estado: draft · Commit: [0-9a-f]{12}',metadata):
        raise ValueError('Metadatos de edición inesperados')
    if value(front[3])!='Esta edición no acredita aprobación institucional ni entrada en vigor.':
        raise ValueError('Declaración institucional inesperada')
    for dest,src_para in zip(cover_paragraphs[1:],front):
        # Preserve the validated cover paragraph style; replace its stale content.
        for child in list(dest):dest.remove(child)
        dest.text=value(src_para)
    section_names=['Declaración Fundacional','Preámbulo']+[f'Capítulo {x}' for x in
                   ('I','II','III','IV','V','VI','VII','VIII','IX')]+['Glosario de XF-000','Referencias']
    chapter_heads=[e for e in headings if any(value(e).startswith(n) for n in section_names)]
    if len(chapter_heads)!=13:raise ValueError('Se esperaban 13 secciones principales')
    # Preserve original source content exactly; change heading style/outline only.
    normative=copy.deepcopy(original_nodes[5:])
    for e in paragraphs(normative):
        if e.tag!=q('t','h'):continue
        if re.match(r'^Artículo\s+\d+\.',value(e)):
            e.set(q('t','outline-level'),'2')
            e.set(q('t','style-name'),'Heading_20_2')
        elif any(value(e).startswith(n) for n in section_names):
            e.set(q('t','outline-level'),'1')
            e.set(q('t','style-name'),'P7')
    for child in list(ob):ob.remove(child)
    for child in ref_nodes[:ref_nodes.index(ref_toc)+1]:
        ob.append(copy.deepcopy(child))
    for child in normative:ob.append(child)
    # Use validated reference's automatic styles and master-page definitions.
    auto=original['content.xml'].find('o:automatic-styles',NS)
    ref_auto=ref['content.xml'].find('o:automatic-styles',NS)
    if auto is None or ref_auto is None:raise ValueError('Estilos automáticos ausentes')
    parent=auto.getparent();parent.replace(auto,copy.deepcopy(ref_auto))
    original['styles.xml']=copy.deepcopy(ref['styles.xml'])
    # Replace TOC cache with empty index-body; UNO must recalculate.
    index=next(x for x in ob if x.tag==q('t','table-of-content'))
    source_index=index.find(q('t','table-of-content-source'))
    source_index.set(q('t','outline-level'),'1')
    index_body=index.find(q('t','index-body'))
    if index_body is not None:
        for child in list(index_body):index_body.remove(child)
    before=[value(e) for e in original_text]
    after=[value(e) for e in paragraphs([x for x in ob if x.tag!=q('t','table-of-content')])]
    # The institutional kicker and index label are the only added strings.
    for extra in ('XIENTIA / BIBLIOTECA FUNDACIONAL','Índice'):
        if extra not in after:raise ValueError('Falta componente editorial '+extra)
        after.remove(extra)
    if before!=after:raise ValueError('Texto original alterado')
    replacements={n:E.tostring(root,encoding='UTF-8',xml_declaration=True)
                  for n,root in original.items()}
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=destination.parent,suffix='.odt');os.close(fd)
    try:
        with zipfile.ZipFile(tmp,'w') as z:
            for info,data in entries:z.writestr(info,replacements.get(info.filename,data))
        with zipfile.ZipFile(tmp) as z:
            if z.testzip():raise ValueError('Salida ODT corrupta')
        os.replace(tmp,destination)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    print('NORMALIZACIÓN OK: 66 artículos; 13 secciones; texto original intacto')
    print('Índice pendiente de actualización UNO:',destination)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True)
    p.add_argument('--reference',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    main(a.input,a.reference,a.output)
