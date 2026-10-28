#!/usr/bin/env python3
"""Optional ODT/PDF renderer for the validated multivolume Markdown builder."""
import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import zipfile
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

VOLUMES = ('XF-000', 'XV-001', 'XEP-0000')


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"Comando falló: {args[0]}\n{result.stderr}\n{result.stdout}")
    return result.stdout


def extra_page_headings(odt, volume):
    """Use the legacy page-heading style for the non-XF front matter, too."""
    if volume == 'XF-000':
        return
    ns = {'office':'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
          'text':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
    with zipfile.ZipFile(odt) as z:
        entries = [(item, z.read(item.filename)) for item in z.infolist()]
    xml = next(data for info,data in entries if info.filename == 'content.xml')
    root = ET.fromstring(xml)
    q = lambda key, local: '{%s}%s' % (ns[key],local)
    headings = {'XV-001': ('Declaración de Visión','Prefacio'),
                'XEP-0000': ('Declaración',)}[volume]
    changed = False
    for h in root.findall('.//text:h', ns):
        title = ''.join(h.itertext()).strip()
        if title in headings or title.startswith('Capítulo ') or title.startswith('Sección '):
            h.set(q('text','style-name'), 'XientiaPageHeading')
            changed = True
    if changed:
        replacement = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        temp = odt.with_suffix('.tmp')
        with zipfile.ZipFile(temp,'w') as z:
            for info, data in entries:
                z.writestr(info, replacement if info.filename == 'content.xml' else data)
        os.replace(temp,odt)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=Path.cwd())
    ap.add_argument('--volume', required=True, choices=VOLUMES)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--format', choices=('odt','pdf','all'), default='all')
    ap.add_argument('--allow-dirty', action='store_true')
    ap.add_argument('--update-index-uno', action='store_true', help='Experimental XF-000 only')
    ap.add_argument('--uno-reference', type=Path, help='ODT de referencia validado')
    args = ap.parse_args()
    if args.update_index_uno:
        if args.volume != 'XF-000' or args.format != 'all':
            ap.error('--update-index-uno requiere --volume XF-000 --format all')
        if not args.uno_reference:
            ap.error('--uno-reference es obligatorio con --update-index-uno')
        from uno_integration import run_experimental
        run_experimental(args, Path(__file__).resolve())
        return
    repo = args.repo.resolve(strict=True)
    out = args.out.resolve()
    script_dir = Path(__file__).resolve().parent
    builder = repo/'tools/editorial/build_library.py'
    legacy = repo/'tools/editorial/build_xientia.py'
    if not builder.is_file() or not legacy.is_file():
        ap.error('Faltan los ensambladores existentes')
    if not shutil.which('pandoc'):
        ap.error('Pandoc no está instalado')
    if args.format in ('pdf','all') and not shutil.which('libreoffice'):
        ap.error('LibreOffice no está instalado')
    cmd = [sys.executable, str(builder), '--repo',str(repo), '--volume',args.volume, '--out',str(out)]
    if args.allow_dirty:
        cmd.append('--allow-dirty')
    print(run(cmd),end='')
    md = out / f'{args.volume}_consulta.md'
    manifest = json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    if manifest['status'] != 'draft' or manifest['edition'] != 'consulta-no-adoptada':
        ap.error('El documento no está identificado como borrador no adoptado')
    odt = out / f'{args.volume}_consulta.odt'
    run(['pandoc',str(md),'-f','markdown','-t','odt','-o',str(odt),'--toc','--toc-depth=2'])
    spec = importlib.util.spec_from_file_location('xientia_legacy',legacy)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.style_odt(odt)
    extra_page_headings(odt,args.volume)
    with zipfile.ZipFile(odt) as z:
        if z.testzip() is not None:
            raise RuntimeError('ODT dañado')
    print('ODT:',odt)
    if args.format in ('pdf','all'):
        pdfdir=out/'pdf'
        pdfdir.mkdir(exist_ok=True)
        # Isolate the LibreOffice profile and remove it even when conversion fails.
        with tempfile.TemporaryDirectory(prefix='xientia-lo-') as profile_dir:
            profile = Path(profile_dir).resolve().as_uri()
            run(['libreoffice',f'-env:UserInstallation={profile}', '--headless',
                 '--convert-to','pdf','--outdir',str(pdfdir),str(odt)])
        pdf=pdfdir/(odt.stem+'.pdf')
        if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):
            raise RuntimeError('No se generó un PDF válido')
        print('PDF:',pdf)
    print('Fuentes Markdown intactas; verificar visualmente ODT/PDF antes de distribuir.')

if __name__ == '__main__':
    main()
