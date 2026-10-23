# Sistema Editorial de Xientia

**Versión:** 0.2.1
**Estado:** herramienta editorial en validación
**Documento compatible:** XF-000 — Constitución de Xientia

## Propósito

El Sistema Editorial de Xientia permite generar ediciones de consulta reproducibles a partir de los documentos Markdown de la Biblioteca Fundacional.

Los archivos Markdown del repositorio constituyen la fuente documental. Las ediciones ODT y PDF son resultados derivados y no sustituyen los originales.

## Requisitos

- Python 3
- Pandoc, para generar ODT
- LibreOffice, para convertir ODT a PDF

## Uso

Desde la raíz del repositorio:

```bash
python3 tools/editorial/build_xientia.py \
  --repo "$PWD" \
  --out /tmp/xientia-editorial-build
```

## Archivos generados

- `XF-000_consulta.md`: documento consolidado.
- `XF-000_consulta.odt`: edición para LibreOffice Writer.
- `pdf/XF-000_consulta.pdf`: edición PDF.
- `manifest.json`: registro de procedencia, versión, estado y hashes SHA-256.

## Validaciones

El ensamblador comprueba la presencia y numeración de los 66 artículos constitucionales, el estado documental y las referencias explícitas a artículos.

La generación del Markdown es reproducible para las mismas fuentes y configuración, según las pruebas realizadas.

Las ediciones ODT y PDF requieren revisión visual antes de distribuirse.

## Estado institucional

XF-000 permanece en versión general `0.1.0-draft`.

Las ediciones generadas son documentos de consulta no adoptados. Su producción no representa aprobación institucional ni entrada en vigor.

## Alcance futuro

Se contempla extender el sistema editorial a XV-001 y XEP-0000, incorporar plantillas institucionales y fortalecer las pruebas automatizadas.

Estas capacidades todavía no forman parte de la versión actual.
