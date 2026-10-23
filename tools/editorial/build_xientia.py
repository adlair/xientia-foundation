#!/usr/bin/env python3
"""Build a traceable consultation edition of XF-000; stdlib-only Markdown core."""
import argparse, hashlib, json, re, subprocess, shutil, zipfile, tempfile, os, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cmd(*args):
    r=subprocess.run(args,text=True,capture_output=True)
    if r.returncode: raise RuntimeError(f"{' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()
def body(path):
    s=path.read_text(encoding='utf-8')
    return re.sub(r'\A---\n.*?\n---\n','',s,flags=re.S).strip()
def metadata(path):
    d={}
    for line in path.read_text(encoding='utf-8').splitlines():
        m=re.match(r'^([a-z_]+):\s*(.*?)\s*$',line)
        if m and m.group(2) not in ('>','|'): d[m.group(1)]=m.group(2).strip('"\'')
    return d
def style_odt(path):
    """Improve pagination and language without changing constitutional text."""
    ns={'office':'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
        'style':'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
        'fo':'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
        'text':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
    for prefix,uri in ns.items(): ET.register_namespace(prefix,uri)
    q=lambda p,n:'{%s}%s'%(ns[p],n)
    with zipfile.ZipFile(path) as z:
        members={n:z.read(n) for n in z.namelist()}
    root=ET.fromstring(members['content.xml'])
    auto=root.find('office:automatic-styles',ns)
    # Keep at least two lines together on both sides of a page boundary.
    for st in auto.findall('style:style',ns):
        if st.get(q('style','family'))!='paragraph': continue
        props=st.find('style:paragraph-properties',ns)
        if props is None: props=ET.SubElement(st,q('style','paragraph-properties'))
        props.set(q('fo','orphans'),'2');props.set(q('fo','widows'),'2')
    st=ET.SubElement(auto,q('style','style'),{
        q('style','name'):'XientiaPageHeading',q('style','family'):'paragraph',
        q('style','parent-style-name'):'Heading_20_1'})
    ET.SubElement(st,q('style','paragraph-properties'),{
        q('fo','break-before'):'page',q('fo','keep-with-next'):'always',
        q('fo','orphans'):'2',q('fo','widows'):'2',
        q('fo','margin-top'):'0.45in',q('fo','margin-bottom'):'0.22in'})
    # For existing article headings, inherit existing visual style, add keep-with-next.
    existing={x.get(q('style','name')):x for x in auto.findall('style:style',ns)}
    article_styles=set()
    for h in root.findall('.//text:h',ns):
        title=''.join(h.itertext()).strip()
        if title.startswith('Capítulo ') or title in ('Declaración Fundacional','Preámbulo','Glosario de XF-000','Referencias'):
            h.set(q('text','style-name'),'XientiaPageHeading')
        elif title.startswith('Artículo '):
            article_styles.add(h.get(q('text','style-name')))
    for name in article_styles:
        if name in existing:
            st=existing[name]
            props=st.find('style:paragraph-properties',ns)
            if props is None: props=ET.SubElement(st,q('style','paragraph-properties'))
            props.set(q('fo','keep-with-next'),'always')
    members['content.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    # Set default proofing language to Spanish (Mexico), including heading styles.
    if 'styles.xml' in members:
        styles=ET.fromstring(members['styles.xml'])
        for st in styles.findall('.//style:default-style',ns)+styles.findall('.//style:style',ns):
            family=st.get(q('style','family'))
            if family not in ('paragraph','text'):continue
            props=st.find('style:text-properties',ns)
            if props is None:props=ET.SubElement(st,q('style','text-properties'))
            props.set(q('fo','language'),'es');props.set(q('fo','country'),'MX')
            if family=='paragraph':
                pp=st.find('style:paragraph-properties',ns)
                if pp is None:pp=ET.SubElement(st,q('style','paragraph-properties'))
                pp.set(q('fo','orphans'),'2');pp.set(q('fo','widows'),'2')
        members['styles.xml']=ET.tostring(styles,encoding='utf-8',xml_declaration=True)
    tmp=path.with_suffix('.tmp')
    with zipfile.ZipFile(tmp,'w') as z:
        for name,data in members.items():
            z.writestr(name,data,compress_type=zipfile.ZIP_STORED if name=='mimetype' else zipfile.ZIP_DEFLATED)
    os.replace(tmp,path)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,default=Path.cwd())
    ap.add_argument('--out',type=Path,default=Path('build/XF-000'))
    ap.add_argument('--allow-dirty',action='store_true')
    args=ap.parse_args(); repo=args.repo.resolve(); out=(repo/args.out).resolve() if not args.out.is_absolute() else args.out
    if not (repo/'docs/XF-000/metadata.yaml').is_file(): ap.error('No se encontró XF-000 en --repo')
    status=cmd('git','-C',str(repo),'status','--porcelain','--untracked-files=no')
    if status and not args.allow_dirty: ap.error('Git tiene cambios rastreados; usar --allow-dirty solo para una edición de prueba')
    commit=cmd('git','-C',str(repo),'rev-parse','HEAD')
    meta=metadata(repo/'docs/XF-000/metadata.yaml')
    if meta.get('status')!='draft': ap.error('El estado del documento debe verificarse antes de publicar una edición no draft')
    root=repo/'docs/XF-000/chapters'
    paths=[root/'00-declaracion-fundacional.md',root/'00-preambulo.md']
    paths += [root/'01-la-ciencia'/f'article-{i:02d}.md' for i in range(1,7)]
    paths += [root/f'{i:02d}-{slug}.md' for i,slug in [(2,'la-mision'),(3,'la-vision'),(4,'principios-fundamentales'),(5,'derechos'),(6,'responsabilidades'),(7,'gobernanza'),(8,'evolucion'),(9,'disposiciones-finales')]]
    paths += [repo/'docs/XF-000/glossary.md',repo/'docs/XF-000/references.md']
    for p in paths:
        if not p.is_file(): ap.error(f'Falta {p}')
    # Structural validation: article numbers 1..66, exactly once.
    articles=[]
    for p in paths:
        articles += [int(x) for x in re.findall(r'^#{1,3} Artículo (\d+)\.',body(p),flags=re.M)]
    if sorted(articles)!=list(range(1,67)): ap.error(f'Numeración inválida: {articles}')
    # Validate explicit internal references without changing constitutional source.
    for p in paths:
        for n in re.findall(r'\bartículo(?:s)?\s+(\d+)\b',body(p),flags=re.I):
            if not 1 <= int(n) <= 66: ap.error(f'Referencia inválida: artículo {n} en {p}')
    chunks=[]
    chunks.append('# Constitución de Xientia\n\n**XF-000 · Edición de consulta — NO ADOPTADA**\n\n'
                  f'**Versión general:** {meta.get("version","desconocida")} · **Estado:** {meta.get("status")} · **Commit:** `{commit[:12]}`\n\n'
                  'Esta edición no acredita aprobación institucional ni entrada en vigor.\n')
    chunks += [body(p) for p in paths[:2]]
    chunks.append('# Capítulo I — La ciencia')
    chunks += [body(p) for p in paths[2:8]]
    chunks += [body(p) for p in paths[8:]]
    text='\n\n'.join(chunks).rstrip()+'\n'
    out.mkdir(parents=True,exist_ok=True)
    md=out/'XF-000_consulta.md'; md.write_text(text,encoding='utf-8')
    manifest={'document':'XF-000','edition':'consulta-no-adoptada','document_version':meta.get('version'),
              'status':meta.get('status'),'git_commit':commit,'dirty_tracked':bool(status),
              'generated_utc':datetime.now(timezone.utc).isoformat(),'article_count':len(articles),
              'sources':{str(p.relative_to(repo)):sha(p) for p in paths},'output_sha256':sha(md)}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Markdown y manifiesto:',out)
    if shutil.which('pandoc'):
        odt=out/'XF-000_consulta.odt'
        cmd('pandoc',str(md),'-f','markdown','-t','odt','-o',str(odt),'--toc','--toc-depth=2')
        style_odt(odt)
        print('ODT:',odt)
        if shutil.which('libreoffice'):
            # PDF via LibreOffice headless; no overwrite of source, distinct output directory.
            pdfdir=out/'pdf';pdfdir.mkdir(exist_ok=True)
            try:
                cmd('libreoffice','-env:UserInstallation=file:///tmp/xientia-editorial-lo-profile','--headless','--convert-to','pdf','--outdir',str(pdfdir),str(odt))
                print('PDF:',pdfdir/(odt.stem+'.pdf'))
            except RuntimeError as e: print('PDF no generado:',e)
    else: print('ODT/PDF no generados: instalar pandoc (y LibreOffice para PDF).')
if __name__=='__main__': main()
