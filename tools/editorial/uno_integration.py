"""Experimental XF-000 full pipeline; no repo source mutations."""
import os
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from normalize_editorial_odt import main as normalize


def run_experimental(args, renderer):
    repo = args.repo.resolve(strict=True)
    target = args.out.resolve()
    reference = args.uno_reference.resolve(strict=True)
    if target.exists():
        raise FileExistsError(f"Salida ya existe: {target}")
    if target == repo or repo in target.parents:
        raise ValueError("La salida debe estar fuera del repositorio")
    if reference == target or target in reference.parents:
        raise ValueError("La referencia no puede estar dentro de la salida")
    if not shutil.which('pandoc') or not shutil.which('libreoffice'):
        raise RuntimeError('Faltan Pandoc o LibreOffice')
    import importlib.util
    for dep in ('uno', 'pymupdf', 'lxml'):
        if importlib.util.find_spec(dep) is None:
            raise RuntimeError(f'Dependencia faltante: {dep}')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.xientia-uno-integration-', dir=target.parent) as d:
        tmp = Path(d)
        build = tmp/'baseline'
        cmd = [sys.executable, str(renderer), '--repo', str(repo),
               '--volume', 'XF-000', '--out', str(build), '--format', 'odt']
        if args.allow_dirty: cmd.append('--allow-dirty')
        subprocess.run(cmd, check=True)
        manifest = json.loads((build/'manifest.json').read_text(encoding='utf-8'))
        expected_commit = manifest['git_commit']
        actual_commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        if expected_commit != actual_commit:
            raise ValueError('Commit del manifiesto no coincide con Git')
        normalized = tmp/'normalized.odt'
        normalize(build/'XF-000_consulta.odt', reference, normalized)
        final = tmp/'uno-output'
        uno_script = renderer.parent/'uno'/'update_toc_uno_r4.py'
        subprocess.run([sys.executable, str(uno_script), '--input', str(normalized),
                        '--reference', str(reference), '--expected-commit', expected_commit, '--out', str(final)], check=True)
        # No public output until all components have been validated.
        (build/'XF-000_consulta.odt').unlink()
        shutil.copy2(final/'XF-000_actualizado.odt',build/'XF-000_consulta.odt')
        (build/'pdf').mkdir()
        shutil.copy2(final/'XF-000_actualizado.pdf',build/'pdf'/'XF-000_consulta.pdf')
        # Directory rename is atomic only when destination does not already exist;
        # this experimental workflow must not be run concurrently for same target.
        from atomic_publish import publish_noreplace
        publish_noreplace(build, target)
    print('UNO EXPERIMENTAL: salida validada en',target)
