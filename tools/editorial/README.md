# Sistema Editorial de Xientia

**Versión de herramientas:** v0.3 (motor multivolumen y renderizador, fase 2)
**Estado:** implementado y probado localmente; revisión editorial y pruebas de conversión adicionales pendientes.
**Volúmenes compatibles:** XF-000, XV-001 y XEP-0000.

## Propósito y fuentes

Los archivos Markdown de `docs/` son las fuentes documentales. El sistema produce ediciones de consulta sin alterar esas fuentes. Los ODT y PDF son derivados; generar una edición no equivale a adoptarla institucionalmente.

## Requisitos

- Python 3 y Git para ensamblar Markdown y generar manifiestos.
- Pandoc para crear ODT.
- LibreOffice para convertir ODT a PDF.
- `unittest` de la biblioteca estándar para las pruebas automatizadas.

Ejecutar desde la raíz de `xientia-foundation`. Mantener las salidas **fuera del repositorio**.

## Comandos

### Motor multivolumen: Markdown y manifiesto

```bash
python3 tools/editorial/build_library.py \
  --repo "$PWD" --volume XV-001 \
  --out /tmp/xientia-build-XV-001
```

Sustituir `XV-001` por `XF-000` o `XEP-0000` según corresponda.

### Renderizador multivolumen: Markdown, ODT y PDF

```bash
python3 tools/editorial/render_library.py \
  --repo "$PWD" --volume XV-001 \
  --out /tmp/xientia-render-XV-001
```

La opción `--format` admite `odt`, `pdf` o `all` (predeterminado). El renderizador utiliza el motor multivolumen para generar las fuentes ensambladas y su manifiesto.

### Ensamblador original de XF-000

```bash
python3 tools/editorial/build_xientia.py \
  --repo "$PWD" --out /tmp/xientia-legacy-XF-000
```

Se conserva por compatibilidad y como referencia de regresión; no es el punto de entrada recomendado para nuevos volúmenes.

### Pruebas

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tools/editorial/tests -v
```

En la última validación local se aprobaron 11 pruebas. Las pruebas actuales no garantizan fidelidad visual ni simulan exhaustivamente errores de LibreOffice.

## Archivos generados

Por volumen: `<ID>_consulta.md`, `manifest.json`, `<ID>_consulta.odt` y `pdf/<ID>_consulta.pdf` cuando se usa el renderizador con formato completo. El manifiesto contiene versión, estado, commit, fuentes y hashes SHA-256 del Markdown; **no certifica** que la representación ODT/PDF sea visualmente perfecta.

## Perfiles y validación

Los perfiles JSON de `tools/editorial/config/` declaran fuentes y orden:

- **XF-000:** Declaración Fundacional, Preámbulo, artículos 1–66, glosario y referencias.
- **XV-001:** Declaración de Visión, Prefacio, capítulos 1–15 y referencias.
- **XEP-0000:** Declaración, secciones 1–11 y referencias.

El motor verifica rutas, duplicados, secuencias documentales y estado `draft`. Los anexos de trabajo no se incorporan automáticamente al cuerpo principal.

## Revisión previa a distribución

Abrir el ODT en LibreOffice y revisar portada, índice, saltos de página, títulos, idioma, líneas viudas, referencias y última página. Comprobar también el PDF exportado y su correspondencia con la edición de consulta. No publicar como documento adoptado sin una decisión institucional real y documentada.

## Limitaciones actuales

No hay garantía de reproducibilidad binaria de ODT/PDF. La fecha de generación del manifiesto puede variar entre ejecuciones. Las fuentes pueden contener marcado Markdown de código para rutas o identificadores bibliográficos, que se mostrará en tipografía monoespaciada. Las pruebas de fallos y la inspección visual completa siguen siendo tareas pendientes.

## Actualización automática del índice mediante UNO (experimental)

El Sistema Editorial de Xientia permite generar una edición de consulta
de XF-000 con actualización automática del índice mediante LibreOffice UNO.

Esta funcionalidad es optativa y no modifica el comportamiento
predeterminado del renderizador multivolumen.

### Requisitos adicionales

- Python con soporte para LibreOffice UNO.
- PyMuPDF.
- lxml.
- LibreOffice y Pandoc.
- Un ODT de referencia editorial previamente validado.

### Ejecución

Desde la raíz del repositorio, ejecutar el renderizador con las opciones
--update-index-uno y --uno-reference.

Ejemplo de ejecución en una sola línea:

    python3 tools/editorial/render_library.py --repo "$PWD" --volume XF-000 --out /tmp/xientia-xf000-uno --update-index-uno --uno-reference /ruta/a/Xientia_XF000_Normalizado_Referencia.odt

La referencia proporciona los estilos y la estructura editorial.
Los metadatos de la edición proceden del documento generado.

El sistema valida los 66 artículos constitucionales, las 13 entradas
del índice, los enlaces internos y la correspondencia del commit Git.

Los documentos derivados se publican únicamente después de superar
las validaciones.

### Limitaciones

- Funcionalidad experimental disponible únicamente para XF-000.
- La salida debe encontrarse fuera del repositorio.
- El directorio de salida no debe existir previamente.
- La referencia editorial debe proporcionarse explícitamente.
- No se garantiza reproducibilidad binaria de ODT/PDF.
- Se requiere inspección visual antes de distribuir.

Las ediciones generadas permanecen en estado de consulta no adoptada.
