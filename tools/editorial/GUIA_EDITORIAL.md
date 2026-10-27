# Guía editorial de Xientia — borrador v0.3

## Principio de integridad

Los Markdown de `docs/` constituyen la fuente documental. Ninguna conversión de formato debe reescribir silenciosamente argumentos, artículos, referencias o decisiones institucionales. Toda corrección sustantiva se revisa en el archivo fuente y queda trazada en Git.

## Voz y estilo

Usar una voz institucional clara, natural y precisa. Evitar solemnidad vacía, fórmulas repetidas sin función y afirmaciones sobre capacidades o autoridades inexistentes. No sustituir automáticamente expresiones normativas como «deberá»: su uso puede ser jurídicamente significativo. La calidad editorial no se mide por detectores de IA.

## Estructura por volumen

- **XF-000:** Declaración Fundacional, Preámbulo, nueve capítulos con 66 artículos, glosario y referencias. El Capítulo I se ensambla a partir de seis archivos.
- **XV-001:** Declaración de Visión, Prefacio y quince capítulos; las referencias van al final.
- **XEP-0000:** Declaración y once secciones; las referencias van al final.

Mantener la secuencia y los títulos propios de cada volumen. No imponer la numeración de artículos de XF-000 a los demás documentos ni incorporar anexos de trabajo por defecto.

## Maquetación

Iniciar las secciones principales en página nueva según su perfil editorial. Mantener los títulos unidos al párrafo siguiente y controlar las líneas viudas y huérfanas. Utilizar español (México) para la revisión lingüística cuando corresponda. Los fragmentos de código, rutas e identificadores pueden mostrarse en monoespaciado sin que ello represente un cambio de contenido.

## Portada, índice y referencias

Cada edición debe mostrar ID, versión, commit y **«Edición de consulta — NO ADOPTADA»** mientras siga en `draft`. Verificar en Writer la actualización del índice y revisar los saltos, la paginación y las páginas finales. No transformar claves bibliográficas en citas formales sin una decisión editorial explícita y verificación de fuentes.

## Control de calidad

Antes de distribuir: ejecutar pruebas automatizadas; comprobar que Git no registre cambios inesperados; verificar manifiesto y SHA-256 del Markdown; abrir ODT y PDF; inspeccionar estructura, legibilidad y ausencia de omisiones. Los hashes del Markdown no acreditan por sí solos fidelidad visual de ODT/PDF.

## Aprobación

La compilación y publicación técnica no implican adopción institucional, entrada en vigor ni revisión jurídica o científica independiente. Los tres volúmenes conservan su estado documental vigente hasta una decisión expresa y verificable.
