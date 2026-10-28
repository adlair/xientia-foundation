#!/usr/bin/env python3
"""Prueba aislada: actualizar índice ODF con LibreOffice UNO y exportar ODT/PDF."""
import argparse
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
import zipfile
import xml.etree.ElementTree as ET

import uno
from com.sun.star.beans import PropertyValue

TEXT = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
Q = lambda name: '{%s}%s' % (TEXT, name)

def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p

def text_of(el):
    return ''.join(el.itertext()).strip()

def inspect(path):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('Archivo ODT dañado')
        root = ET.fromstring(archive.read('content.xml'))
    headings = root.findall('.//' + Q('h'))
    articles = [int(m.group(1)) for h in headings if (m := re.match(r'^Artículo (\d+)\.', text_of(h)))]
    main = [h for h in headings if h.get(Q('outline-level')) == '1']
    toc = root.find('.//' + Q('table-of-content'))
    if toc is None:
        raise RuntimeError('Índice ausente')
    source = toc.find(Q('table-of-content-source'))
    if source is None or source.get(Q('outline-level')) != '1':
        raise RuntimeError('Profundidad de índice distinta de 1')
    entries = toc.findall('.//' + Q('index-body') + '/' + Q('p'))
    # LibreOffice puede generar entradas como párrafos anidados dentro de la sección.
    body = toc.find(Q('index-body'))
    cached = [text_of(p) for p in body.iter(Q('p'))] if body is not None else []
    if sorted(articles) != list(range(1, 67)) or len(main) != 13:
        raise RuntimeError(f'Encabezados inesperados: {len(articles)} artículos, {len(main)} secciones')
    return cached

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--timeout', type=int, default=30)
    args = ap.parse_args()
    source = args.input.resolve()
    if not source.is_file():
        ap.error('No existe ODT de entrada')
    if args.out.resolve() == source.parent or source == (args.out / 'XF-000_actualizado.odt').resolve():
        ap.error('El directorio de salida debe ser distinto del de entrada')
    inspect(source)
    args.out.mkdir(parents=True, exist_ok=True)
    odt = args.out / 'XF-000_actualizado.odt'
    pdf = args.out / 'XF-000_actualizado.pdf'
    with tempfile.TemporaryDirectory(prefix='xientia-uno-') as tmp:
        profile = Path(tmp) / 'profile'
        port = free_port()
        command = [shutil.which('libreoffice') or 'libreoffice',
                   '-env:UserInstallation=' + profile.as_uri(), '--headless',
                   '--norestore', '--nodefault', '--nofirststartwizard',
                   '--accept=socket,host=127.0.0.1,port=%d;urp;StarOffice.ServiceManager' % port]
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        doc = None
        try:
            ctx = uno.getComponentContext()
            resolver = ctx.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', ctx)
            remote = None
            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError('LibreOffice terminó antes de establecer conexión')
                try:
                    remote = resolver.resolve('uno:socket,host=127.0.0.1,port=%d;urp;StarOffice.ComponentContext' % port)
                    break
                except Exception:
                    time.sleep(.2)
            if remote is None:
                raise RuntimeError('Tiempo de espera agotado para UNO')
            desktop = remote.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', remote)
            doc = desktop.loadComponentFromURL(uno.systemPathToFileUrl(str(source)), '_blank', 0,
                                               (prop('Hidden', True), prop('ReadOnly', False),
                                                prop('UpdateDocMode', 3), prop('MacroExecutionMode', 4)))
            if doc is None:
                raise RuntimeError('No se pudo abrir el ODT')
            indexes = doc.getDocumentIndexes()
            if indexes.getCount() != 1:
                raise RuntimeError('Se esperaba exactamente un índice')
            indexes.getByIndex(0).update()
            doc.refresh()
            doc.getTextFields().refresh()
            indexes.getByIndex(0).update()
            doc.storeAsURL(uno.systemPathToFileUrl(str(odt.resolve())),
                           (prop('FilterName', 'writer8'), prop('Overwrite', True)))
            doc.storeToURL(uno.systemPathToFileUrl(str(pdf.resolve())),
                           (prop('FilterName', 'writer_pdf_Export'), prop('Overwrite', True)))
        finally:
            if doc is not None:
                try: doc.close(True)
                except Exception:
                    try: doc.dispose()
                    except Exception: pass
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
    cached = inspect(odt)
    print('Entradas cacheadas:', len(cached))
    for item in cached: print('  ', item)
    if len(cached) != 13 or any('Artículo ' in item for item in cached):
        raise RuntimeError('El índice guardado no contiene exactamente 13 entradas principales')
    if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):
        raise RuntimeError('PDF no generado correctamente')
    print('ODT:', odt)
    print('PDF:', pdf)
    print('Prueba UNO terminada; verificar paginación y enlaces visualmente')

if __name__ == '__main__':
    main()
