#!/usr/bin/env python3
"""Non-destructive multivolume Markdown builder for Xientia (v0.3 preview)."""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

VOLUMES = ('XF-000', 'XV-001', 'XEP-0000')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def content(path):
    raw = path.read_text(encoding='utf-8')
    return re.sub(r'\A---\r?\n.*?\r?\n---\r?\n', '', raw, flags=re.S).strip()

def metadata(path):
    result = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        match = re.match(r'^([a-z_]+):\s*(.*?)\s*$', line)
        if match and match.group(2) not in ('>', '|'):
            result[match.group(1)] = match.group(2).strip('"\'')
    return result

def run_git(repo, *args):
    proc = subprocess.run(['git', '-C', str(repo), *args], text=True, capture_output=True, check=True)
    return proc.stdout.strip()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--volume', choices=VOLUMES, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--config-dir', type=Path, default=None)
    parser.add_argument('--allow-dirty', action='store_true')
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    out = args.out.resolve()
    config_dir = (args.config_dir or Path(__file__).parent / 'config').resolve()
    config = json.loads((config_dir / f'{args.volume}.json').read_text(encoding='utf-8'))
    if config.get('id') != args.volume:
        parser.error('El ID del perfil no coincide con --volume')
    try:
        status = run_git(repo, 'status', '--porcelain', '--untracked-files=no')
        commit = run_git(repo, 'rev-parse', 'HEAD')
    except subprocess.CalledProcessError as exc:
        parser.error(f'No se pudo consultar Git: {exc.stderr.strip()}')
    if status and not args.allow_dirty:
        parser.error('Git tiene cambios rastreados; usar --allow-dirty solo para pruebas')
    paths = []
    seen = set()
    def add(rel):
        if not isinstance(rel, str) or not rel.endswith('.md'):
            parser.error(f'Ruta de fuente inválida: {rel!r}')
        path = (repo / rel).resolve()
        if not path.is_relative_to(repo) or not path.is_file():
            parser.error(f'Ruta ausente o fuera del repositorio: {rel}')
        if path in seen:
            parser.error(f'Fuente duplicada: {rel}')
        seen.add(path)
        paths.append((rel, path))
    for key in ('prefix', 'chapter_1_files', 'chapter_files', 'suffix'):
        for rel in config.get(key, []):
            add(rel)
    meta_rel = config.get('metadata')
    if not isinstance(meta_rel, str):
        parser.error('Falta metadata')
    meta_path = (repo / meta_rel).resolve()
    if not meta_path.is_relative_to(repo) or not meta_path.is_file():
        parser.error('Ruta de metadatos inválida')
    meta = metadata(meta_path)
    if meta.get('id') != args.volume or meta.get('status') != 'draft':
        parser.error('ID o estado de metadatos inesperado; solo se generan ediciones draft')
    rule = config['validation']
    if rule['kind'] == 'article_sequence':
        numbers = []
        for _, path in paths:
            numbers.extend(int(n) for n in re.findall(r'^#{1,3}\s+Artículo\s+(\d+)\.', content(path), re.M))
        expected = list(range(rule['first'], rule['last'] + 1))
        if numbers != expected:
            parser.error(f'Secuencia de artículos inválida: {numbers}')
        for rel, path in paths:
            for n in re.findall(r'\bartículo(?:s)?\s+(\d+)\b', content(path), re.I):
                if int(n) not in expected:
                    parser.error(f'Referencia fuera de rango: artículo {n} en {rel}')
    elif rule['kind'] == 'chapter_sequence':
        chapters = config['chapter_files']
        expected = list(range(rule['first'], rule['last'] + 1))
        actual = []
        for rel in chapters:
            match = re.search(r'/chapters/(\d+)-[^/]+\.md$', rel)
            if not match:
                parser.error(f'Nombre de capítulo inválido: {rel}')
            actual.append(int(match.group(1)))
        if actual != expected:
            parser.error(f'Secuencia de capítulos inválida: {actual}')
        if len(chapters) != len(expected):
            parser.error('Número incorrecto de capítulos')
    else:
        parser.error(f'Regla desconocida: {rule["kind"]}')
    title = {'XF-000':'Constitución de Xientia', 'XV-001':'Vision Paper de Xientia',
             'XEP-0000':'Proceso de Evolución de Xientia'}[args.volume]
    header = (f'# {title}\n\n**{args.volume} · Edición de consulta — NO ADOPTADA**\n\n'
              f'**Versión general:** {meta.get("version")} · **Estado:** draft · **Commit:** `{commit[:12]}`\n\n'
              'Esta edición no acredita aprobación institucional ni entrada en vigor.')
    chunks = [header]
    for i, (rel, path) in enumerate(paths):
        if args.volume == 'XF-000' and i == len(config['prefix']):
            chunks.append('# ' + config['chapter_1_heading'])
        chunks.append(content(path))
    assembled = '\n\n'.join(chunks).rstrip() + '\n'
    # Avoid emitting a build inside the source tree by default; require explicit confirmation if desired.
    if out == repo or out.is_relative_to(repo):
        parser.error('La salida debe estar fuera del repositorio')
    out.mkdir(parents=True, exist_ok=True)
    md = out / f'{args.volume}_consulta.md'
    md.write_text(assembled, encoding='utf-8')
    manifest = {
        'document': args.volume, 'edition': 'consulta-no-adoptada',
        'document_version': meta.get('version'), 'status': meta.get('status'),
        'git_commit': commit, 'dirty_tracked': bool(status),
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'validation': rule, 'sources': {rel: digest(path.read_bytes()) for rel, path in paths},
        'metadata_source': {meta_rel: digest(meta_path.read_bytes())},
        'output_sha256': digest(md.read_bytes()),
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Markdown y manifiesto: {out}')
    print(f'SHA-256: {manifest["output_sha256"]}')
    print('ODT/PDF: no incluidos en esta fase; build_xientia.py permanece disponible para XF-000')

if __name__ == '__main__':
    main()
