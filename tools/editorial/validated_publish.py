"""Opt-in validated, atomic publishing for XV-001 and XEP-0000.

The existing renderer remains the source of ODT/PDF artifacts. Publication
is performed only after independent structural and PDF correspondence checks.
"""
import json
import hashlib
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from atomic_publish import publish_noreplace
from odt_structure import validate_odt
from pdf_correspondence import validate_odt_pdf
from volume_profiles import load_profile

SUPPORTED = ("XV-001", "XEP-0000")


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def git_commit(repo):
    return subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()


def run_supervised(cmd):
    """Terminate our own process group on interruption or conversion failure."""
    process = subprocess.Popen(cmd, start_new_session=True)
    try:
        code = process.wait()
        if code:
            raise subprocess.CalledProcessError(code, cmd)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        raise


def publish_validated(args, renderer):
    if args.volume not in SUPPORTED or args.format != "all":
        raise ValueError("--validate-publish requiere XV-001 o XEP-0000 y --format all")
    repo = args.repo.resolve(strict=True)
    out = args.out.resolve()
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"La salida ya existe: {out}")
    if not out.parent.is_dir():
        raise FileNotFoundError(out.parent)
    if out.is_relative_to(repo):
        raise ValueError("La salida no puede estar dentro del repositorio")
    profile = load_profile(renderer.parent / "config", args.volume)
    # Use a sibling staging directory for same-filesystem atomic rename.
    with tempfile.TemporaryDirectory(prefix=".xientia-f42-", dir=out.parent) as temp:
        stage = Path(temp) / "publication"
        cmd = [sys.executable, str(renderer), "--repo", str(repo),
               "--volume", args.volume, "--out", str(stage), "--format", "all"]
        if args.allow_dirty:
            cmd.append("--allow-dirty")
        run_supervised(cmd)
        odt = stage / f"{args.volume}_consulta.odt"
        pdf = stage / "pdf" / f"{args.volume}_consulta.pdf"
        manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("document") != args.volume or manifest.get("status") != "draft" or manifest.get("edition") != "consulta-no-adoptada":
            raise ValueError("Manifiesto no corresponde al borrador esperado")
        if profile["validation"]["editorial"]["publication_status"] != manifest["status"]:
            raise ValueError("Estado incompatible con perfil")
        if manifest.get('git_commit') != git_commit(repo):
            raise ValueError('Commit del manifiesto no coincide con Git')
        if not args.allow_dirty and manifest.get('dirty_tracked') is not False:
            raise ValueError('Manifiesto de repositorio limpio inválido')
        markdown = stage / f'{args.volume}_consulta.md'
        if manifest.get('output_sha256') != sha256_file(markdown):
            raise ValueError('SHA-256 Markdown no coincide con manifiesto')
        if not odt.is_file() or not pdf.is_file():
            raise FileNotFoundError('ODT o PDF ausente')
        # Record hashes before validation; detect changes between validation and publication.
        artifact_hashes = {str(p.relative_to(stage)): sha256_file(p) for p in (markdown, odt, pdf)}
        structure = validate_odt(args.volume, odt)
        correspondence = validate_odt_pdf(args.volume, odt, pdf)
        if structure["chapters"] != profile["validation"]["last"]:
            raise ValueError("Capítulos no corresponden al perfil")
        if structure["headings"] != correspondence["headings"]:
            raise ValueError("Correspondencia incompleta")
        for name, expected in artifact_hashes.items():
            if sha256_file(stage / name) != expected:
                raise ValueError(f'Archivo alterado durante validación: {name}')
        # Refuse replacement even if another process creates out during validation.
        publish_noreplace(stage, out)
        print(f"PUBLICACIÓN VALIDADA: {args.volume}: {out}")
        print(f"Capítulos: {structure['chapters']}; artículos: {structure['articles']}; páginas PDF: {correspondence['pages']}")
