#!/usr/bin/env python3
"""Opt-in end-to-end concurrency audit; never modifies the repository."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def terminate_group(proc):
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--volume', choices=('XV-001', 'XEP-0000'), required=True)
    parser.add_argument('--workspace-parent', type=Path, default=Path('/tmp'))
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    parent = args.workspace_parent.resolve(strict=True)
    if args.timeout < 10:
        parser.error('timeout must be at least 10 seconds')
    renderer = repo / 'tools/editorial/render_library.py'
    if not renderer.is_file():
        parser.error('renderer not found')
    commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain'], text=True).strip():
        parser.error('repository must be clean')
    workspace = Path(tempfile.mkdtemp(prefix='xientia-f42-r4-', dir=parent))
    dest = workspace / 'published'
    workers = {}
    report = {'phase': 'F4.2-R4', 'volume': args.volume, 'commit': commit,
              'workspace': str(workspace), 'status': 'started', 'workers': {}}
    print('AUDIT WORKSPACE:', workspace, flush=True)
    try:
        for label in ('A', 'B'):
            cmd = [sys.executable, str(renderer), '--repo', str(repo), '--volume', args.volume,
                   '--out', str(dest), '--validate-publish']
            with (workspace / f'{label}.stdout.log').open('w') as stdout, (workspace / f'{label}.stderr.log').open('w') as stderr:
                proc = subprocess.Popen(cmd, cwd=repo, stdout=stdout, stderr=stderr,
                                        start_new_session=True,
                                        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            workers[label] = proc
            report['workers'][label] = {'pid': proc.pid, 'pgid': proc.pid}
        deadline = time.monotonic() + args.timeout
        while any(p.poll() is None for p in workers.values()):
            if time.monotonic() >= deadline:
                raise TimeoutError('audit timeout')
            time.sleep(.1)
        for label, proc in workers.items():
            report['workers'][label]['returncode'] = proc.returncode
        winners = [label for label, p in workers.items() if p.returncode == 0]
        losers = [label for label, p in workers.items() if p.returncode != 0]
        if len(winners) != 1 or len(losers) != 1:
            raise RuntimeError('expected exactly one winner and one loser')
        loser_log = (workspace / f'{losers[0]}.stderr.log').read_text(errors='replace')
        if 'FileExistsError' not in loser_log:
            raise RuntimeError('loser did not fail with FileExistsError')
        manifest = json.loads((dest / 'manifest.json').read_text(encoding='utf-8'))
        if not (manifest.get('document') == args.volume and manifest.get('status') == 'draft'
                and manifest.get('git_commit') == commit and manifest.get('dirty_tracked') is False):
            raise RuntimeError('manifest provenance mismatch')
        artifacts = [f'{args.volume}_consulta.md', f'{args.volume}_consulta.odt',
                     f'pdf/{args.volume}_consulta.pdf']
        report['sha256'] = {}
        for rel in artifacts:
            path = dest / rel
            if not path.is_file() or not path.stat().st_size:
                raise RuntimeError(f'missing or empty artifact: {rel}')
            report['sha256'][rel] = sha256(path)
        sys.path.insert(0, str(repo / 'tools/editorial'))
        from odt_structure import validate_odt
        from pdf_correspondence import validate_odt_pdf
        odt = dest / artifacts[1]
        pdf = dest / artifacts[2]
        structure = validate_odt(args.volume, odt)
        correspondence = validate_odt_pdf(args.volume, odt, pdf)
        from volume_profiles import load_profile

        profile = load_profile(
            repo / 'tools/editorial/config',
            args.volume
        )

        rule = profile['validation']

        if rule['kind'] != 'chapter_sequence':
            raise RuntimeError('unexpected validation kind')

        if structure['chapters'] != rule['last']:
            raise RuntimeError('chapter count mismatch')

        if structure['headings'] != correspondence['headings']:
            raise RuntimeError('ODT/PDF heading mismatch')

        if structure['chapters'] != correspondence['chapters']:
            raise RuntimeError('ODT/PDF chapter mismatch')

        if structure['articles'] != correspondence['articles']:
            raise RuntimeError('ODT/PDF article mismatch')
        report['structure'] = structure
        report['correspondence'] = correspondence

        # Detectar alteraciones durante las validaciones.
        for rel, expected_hash in report['sha256'].items():
            actual_hash = sha256(dest / rel)
            if actual_hash != expected_hash:
                raise RuntimeError(
                    f'artifact changed during validation: {rel}'
                )

        report['integrity_rechecked'] = True

        if list(workspace.glob('.xientia-f42-*')):
            raise RuntimeError('residual staging directories')
        report['validation_completed'] = True
    except BaseException as exc:
        report['status'] = 'failed'
        report['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        cleanup_errors = []

        for label, proc in workers.items():
            try:
                if proc.poll() is None:
                    terminate_group(proc)
                proc.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired) as exc:
                cleanup_errors.append(
                    f'{label}: {type(exc).__name__}: {exc}'
                )

            report['workers'][label]['returncode'] = proc.poll()

        # Linux: comprobar miembros activos de los grupos propios.
        for label, proc in workers.items():
            pgid = report['workers'][label]['pgid']
            members = []

            for entry in Path('/proc').iterdir():
                if not entry.name.isdigit():
                    continue

                try:
                    stat = (entry / 'stat').read_text()
                    fields = stat.rsplit(') ', 1)[1].split()
                    state = fields[0]
                    process_group = int(fields[2])

                    if process_group == pgid and state not in ('Z', 'X'):
                        members.append(int(entry.name))
                except (OSError, ValueError, IndexError):
                    continue

            if members:
                cleanup_errors.append(
                    f'{label}: active process group members: {members}'
                )

        report['cleanup'] = {
            'checked': True,
            'errors': cleanup_errors,
        }

        if cleanup_errors:
            report['status'] = 'failed'
            report['error'] = 'operational cleanup incomplete'
        elif report.get('validation_completed') is True and report.get('status') != 'failed':
            report['status'] = 'passed'

        (workspace / 'report.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str)
            + '\n',
            encoding='utf-8'
        )

        print(
            'AUDIT RESULT:',
            report['status'],
            'REPORT:',
            workspace / 'report.json',
            flush=True
        )

        if cleanup_errors:
            raise RuntimeError(
                'Auditor cleanup failed: ' + '; '.join(cleanup_errors)
            )


if __name__ == '__main__':
    main()
