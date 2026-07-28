---
document: XEP-0000
chapter: 8
title: Versionado y trazabilidad
version: 0.1.0
status: draft
language: es-MX
---

# Capítulo VIII — Versionado y trazabilidad

## Artículo 21. Versionado

Los XEP utilizarán versionado semántico:

`MAJOR.MINOR.PATCH`

- `MAJOR`: cambio incompatible o reforma sustantiva;
- `MINOR`: incorporación significativa compatible;
- `PATCH`: corrección editorial o aclaración sin cambio normativo.

## Artículo 22. Relación con documentos afectados

Cuando un XEP aceptado modifique un documento fundacional:

1. el documento afectado deberá citar el XEP;
2. el XEP deberá indicar la versión anterior y la nueva;
3. el historial del documento deberá registrar la modificación;
4. la versión sustituida deberá conservarse;
5. el cambio deberá vincularse con el commit que lo implementó.

## Artículo 23. Prohibición de borrado histórico

Los XEP rechazados, retirados, sustituidos o históricos no deberán eliminarse.

Su conservación permite comprender la evolución de las decisiones y evita que
se pierdan alternativas, errores o aprendizajes relevantes.

## Artículo 24. Identificadores

Cada XEP tendrá un identificador estable.

La representación canónica será `XEP-0000`.

En el futuro podrá asociarse con una URI persistente como
`xientia://xep/0000`. La URI futura no sustituirá al identificador documental.
