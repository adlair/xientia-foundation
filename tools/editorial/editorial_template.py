"""Resolve and integrity-check the experimental XF-000 style reference."""
import hashlib
import json
from pathlib import Path
import zipfile

def resolve_template(editorial_dir, override=None):
    if override is not None:
        path = Path(override).expanduser().resolve(strict=True)
    else:
        folder = Path(editorial_dir) / "templates" / "XF-000"
        manifest = json.loads((folder / "template.json").read_text(encoding="utf-8"))
        if manifest.get("volume") != "XF-000" or manifest.get("status") != "experimental":
            raise ValueError("Perfil de plantilla inesperado")
        filename = manifest.get("reference_file")
        if filename != "reference.odt":
            raise ValueError("Ruta de plantilla inesperada")
        path = folder / filename
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != manifest.get("sha256"):
            raise ValueError("SHA-256 de plantilla no coincide")
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise ValueError("Referencia ODT inexistente o inválida")
    with zipfile.ZipFile(path) as z:
        if z.testzip() or "content.xml" not in z.namelist() or "styles.xml" not in z.namelist():
            raise ValueError("Referencia ODT corrupta")
    return path
