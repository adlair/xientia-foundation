"""Experimental profile contract for Xientia's three editorial volumes.

This module does not change build_library.py or UNO.
"""
import json
from pathlib import Path

VOLUMES = ("XF-000", "XV-001", "XEP-0000")
KINDS = {"article_sequence", "chapter_sequence"}

def load_profile(config_dir, volume):
    if volume not in VOLUMES:
        raise ValueError("Volumen desconocido")
    profile = json.loads((Path(config_dir) / (volume + ".json")).read_text(encoding="utf-8"))
    validate_profile(profile, volume)
    return profile

def validate_profile(profile, volume):
    if profile.get("id") != volume:
        raise ValueError("ID del perfil incorrecto")
    rule = profile.get("validation")
    if not isinstance(rule, dict) or rule.get("kind") not in KINDS:
        raise ValueError("Tipo de validación desconocido")
    first, last = rule.get("first"), rule.get("last")
    if type(first) is not int or type(last) is not int or first != 1 or last < first:
        raise ValueError("Rango de secuencia inválido")
    expected = {"XF-000": ("article_sequence", 66),
                "XV-001": ("chapter_sequence", 15),
                "XEP-0000": ("chapter_sequence", 11)}
    if (rule["kind"], last) != expected[volume]:
        raise ValueError("Regla incompatible con volumen")
    editorial = rule.get("editorial")
    if not isinstance(editorial, dict) or editorial != {
        "cover": "dynamic", "toc": "top_level", "publication_status": "draft"
    }:
        raise ValueError("Contrato editorial inválido")
    if rule["kind"] == "chapter_sequence":
        paths = profile.get("chapter_files")
        if not isinstance(paths, list) or len(paths) != last:
            raise ValueError("Cantidad de archivos de capítulos inválida")
        import re
        actual = []
        for path in paths:
            if not isinstance(path, str):
                raise ValueError("Ruta de capítulo inválida")
            match = re.search(r"/chapters/(\d+)-[^/]+\.md$", path)
            if not match:
                raise ValueError("Ruta de capítulo inválida")
            actual.append(int(match.group(1)))
        if actual != list(range(1, last+1)):
            raise ValueError("Secuencia de archivos inválida")
    return True

def validate_numbers(profile, numbers):
    rule = profile["validation"]
    expected = list(range(rule["first"], rule["last"] + 1))
    if list(numbers) != expected:
        raise ValueError("Secuencia documental inválida")
    return True
