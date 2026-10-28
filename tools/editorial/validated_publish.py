"""Opt-in validated, atomic publishing for XV-001 and XEP-0000.

The existing renderer remains the source of ODT/PDF artifacts. Publication
is performed only after independent structural and PDF correspondence checks.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from atomic_publish import publish_noreplace
from odt_structure import validate_odt
from pdf_correspondence import validate_odt_pdf
from volume_profiles import load_profile

SUPPORTED = ("XV-001", "XEP-0000")


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
        subprocess.run(cmd, check=True)
        odt = stage / f"{args.volume}_consulta.odt"
        pdf = stage / "pdf" / f"{args.volume}_consulta.pdf"
        manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("document") != args.volume or manifest.get("status") != "draft" or manifest.get("edition") != "consulta-no-adoptada":
            raise ValueError("Manifiesto no corresponde al borrador esperado")
        if profile["validation"]["editorial"]["publication_status"] != manifest["status"]:
            raise ValueError("Estado incompatible con perfil")
        structure = validate_odt(args.volume, odt)
        correspondence = validate_odt_pdf(args.volume, odt, pdf)
        if structure["chapters"] != profile["validation"]["last"]:
            raise ValueError("Capítulos no corresponden al perfil")
        if structure["headings"] != correspondence["headings"]:
            raise ValueError("Correspondencia incompleta")
        # Refuse replacement even if another process creates out during validation.
        publish_noreplace(stage, out)
        print(f"PUBLICACIÓN VALIDADA: {args.volume}: {out}")
        print(f"Capítulos: {structure['chapters']}; artículos: {structure['articles']}; páginas PDF: {correspondence['pages']}")
