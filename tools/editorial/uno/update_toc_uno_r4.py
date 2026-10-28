#!/usr/bin/env python3
"""UNO R4: supervised XF-000 conversion, validate before directory publication."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from atomic_publish import publish_noreplace
import importlib.util
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile

NAMES = ('XF-000_actualizado.odt', 'XF-000_actualizado.pdf')


def preflight(source, out, reference, timeout):
    if timeout <= 0:
        raise ValueError('El tiempo de espera debe ser positivo')
    if not source.is_file():
        raise FileNotFoundError(source)
    if out.exists():
        raise FileExistsError(f'La ruta de salida ya existe: {out}')
    if not out.parent.is_dir():
        raise FileNotFoundError(f'Falta directorio padre de salida: {out.parent}')
    if source == out or source.is_relative_to(out):
        raise ValueError('La salida contiene la entrada')
    if reference is not None and (not reference.is_file() or reference.is_relative_to(out)):
        raise ValueError('Referencia inválida')
    if shutil.which('libreoffice') is None:
        raise RuntimeError('Falta LibreOffice')
    for module in ('uno', 'pymupdf'):
        if importlib.util.find_spec(module) is None:
            raise RuntimeError(f'Falta dependencia: {module}')
    for file in (source, reference):
        if file is None:
            continue
        with zipfile.ZipFile(file) as archive:
            if archive.testzip() is not None or 'content.xml' not in archive.namelist():
                raise ValueError(f'ODT inválido: {file}')


def terminate_group(process, grace=3):
    """Only signal the process group created by our own subprocess."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    # Even if the group leader exited, descendants might still be running.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass


def supervise(cmd, timeout):
    process = subprocess.Popen(cmd, start_new_session=True)
    try:
        code = process.wait(timeout=timeout)
        if code != 0:
            raise subprocess.CalledProcessError(code, cmd)
    except BaseException:
        terminate_group(process)
        raise


def publish(stage, out):
    if out.exists():
        raise FileExistsError(out)
    for name in NAMES:
        if not (stage / name).is_file():
            raise RuntimeError(f'Falta resultado validado: {name}')
    # Stage is created as sibling of out, so directory rename stays on one FS.
    publish_noreplace(stage, out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--expected-commit', type=str)
    parser.add_argument('--timeout', type=int, default=30)
    args = parser.parse_args()
    source, out = args.input.resolve(), args.out.resolve()
    reference = args.reference.resolve() if args.reference else None
    preflight(source, out, reference, args.timeout)
    from validate_uno_r2 import validate
    with tempfile.TemporaryDirectory(prefix='.xientia-r4-', dir=out.parent) as tmp:
        stage = Path(tmp) / 'publication'
        cmd = [sys.executable, str(Path(__file__).with_name('update_toc_uno_r1.py')),
               '--input', str(source), '--out', str(stage), '--timeout', str(args.timeout)]
        supervise(cmd, args.timeout + 120)
        validate(stage / NAMES[0], stage / NAMES[1], source, args.expected_commit)
        publish(stage, out)
    print('UNO R4: documentos validados y publicados:', out)


if __name__ == '__main__':
    main()
