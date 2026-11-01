# Xientia Foundation — Auditoría técnica de cierre F4.3

**Identificador:** XIENTIA-F43-TECHNICAL-CLOSURE-AUDIT
**Versión del informe:** 1.0
**Fecha de emisión:** 2026-10-31 (México; la ejecución de CI se registra en GitHub como 2026-11-01 UTC)
**Proyecto:** `adlair/xientia-foundation`
**Fase:** F4.3 — Automatización editorial y trazabilidad
**Dictamen:** **GO — cierre del alcance técnico auditado**, con riesgos residuales documentados
**Naturaleza:** Informe técnico; **no** es un acto de adopción institucional.

## 1. Resumen ejecutivo

La fase F4.3 incorpora integración continua editorial, contrato y esquema de evidencias, verificación de procedencia e integridad, generación de `evidence.json` y publicación exclusiva de paquetes completos de consulta para XV-001 y XEP-0000. La auditoría se efectuó a partir de un clon limpio del repositorio y contrastó el contrato declarado con la implementación y las ejecuciones observadas.

**Resultado:** 114 de 114 pruebas editoriales aprobadas en el clon de auditoría; publicación y verificación independiente de XV-001 y XEP-0000 aprobadas; corrección de la automatización de `main` integrada y ejecución posterior de GitHub Actions con resultado `success`, incluido el paso **Build and verify consultation editions on main**.

El dictamen GO corresponde al **alcance técnico F4.3**. No certifica durabilidad absoluta frente a fallos físicos, recuperación automática de staging tras terminación abrupta, aislamiento ante actores maliciosos concurrentes, ni aprobación o publicación institucional de documentos.

## 2. Línea base y alcance

| Elemento | Referencia |
| --- | --- |
| Repositorio | https://github.com/adlair/xientia-foundation |
| Rama auditada | `main` |
| Base de auditoría de regresión y paquetes | `e0f8167b12edf0f02d028caee997d164b47014bc` |
| Commit final de cierre y corrección CI | `b631ac74de49a7cbc0d9999eb81d349bfa889df0` |
| Motor de publicación | `tools/editorial/validated_publish.py`, `tools/editorial/atomic_publish.py` |
| Generación y verificación | `tools/editorial/ci/evidence_generate.py`, `evidence_verify.py`, `evidence_schema.py` |
| Workflow | `.github/workflows/editorial-ci.yml` |
| Contrato | `tools/editorial/ci/editorial_ci_contract.json` |
| Volúmenes de evidencia R2 | `XV-001`, `XEP-0000` |
| Volumen fuera del esquema R2 | `XF-000` (conserva su flujo editorial anterior) |

La auditoría cubre la integración y controles de F4.3; no constituye una revisión jurídica, científica, política o institucional del contenido de los textos fundacionales. Los documentos conservan **`draft`**, edición **`consulta-no-adoptada`** y **`institutional_adoption: false`**.

## 3. Integraciones verificadas

| PR | Cambio | Commit de fusión | Estado |
| --- | --- | --- | --- |
| [#1](https://github.com/adlair/xientia-foundation/pull/1) | Workflow de validación editorial | `afe1e224f4be` | Fusionado |
| [#2](https://github.com/adlair/xientia-foundation/pull/2) | Esquema de validación de evidencias | `0fb21ac30085` | Fusionado |
| [#3](https://github.com/adlair/xientia-foundation/pull/3) | Verificador endurecido de evidencias | `91277ed8173c` | Fusionado |
| [#4](https://github.com/adlair/xientia-foundation/pull/4) | Generador de evidencias validadas | `e4583a39293c` | Fusionado |
| [#5](https://github.com/adlair/xientia-foundation/pull/5) | Publicación atómica con evidencias | `e0f8167b12ed` | Fusionado |
| [#6](https://github.com/adlair/xientia-foundation/pull/6) | Cumplimiento de CI en `main` | `b631ac74de49` | Fusionado |

## 4. Metodología y evidencias

### 4.1 Integridad de la línea base

Se creó un clon aislado de `main` en `/tmp/xientia-f43-closure-audit`. Se verificaron `git rev-parse HEAD`, `git status --porcelain` y `git diff --check`. El clon de referencia correspondía a `e0f8167...` y estaba limpio antes de ejecutar las comprobaciones.

### 4.2 Regresión editorial

Comando de auditoría:

```bash
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tools/editorial/tests -v
```

**Resultado observado:** `Ran 114 tests in 34.943s` — `OK`. Incluye pruebas de esquema, generación, verificación, publicación, concurrencia, fallos e interrupción gestionada. Esta cifra corresponde a la ejecución local de la base `e0f8167...`; el workflow posterior en `main` también completó satisfactoriamente su paso de regresión, sin que este informe atribuya un conteo separado extraído de sus logs.

### 4.3 Publicación y verificación de consulta

Se ejecutó para cada volumen el publicador con:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/editorial/render_library.py \
  --repo "$PWD" --volume XV-001 \
  --out /tmp/xientia-f43-audit-xv \
  --validate-publish --publish-with-evidence
```

El mismo procedimiento se repitió con `XEP-0000` y destino `/tmp/xientia-f43-audit-xep`. Después, `verify_package()` verificó independientemente las evidencias y los artefactos. Ambos paquetes conservaron la procedencia `e0f8167b12ed...`, estado `draft` y ausencia de adopción institucional.

| Resultado | XV-001 | XEP-0000 |
| --- | ---: | ---: |
| Publicación validada | PASS | PASS |
| Verificación independiente | PASS | PASS |
| Artefactos de contenido verificados (MD/ODT/PDF) | 3 | 3 |
| Capítulos ODT | 15 | 11 |
| Artículos ODT | 0 | 33 |
| Páginas PDF | 52 | 16 |
| `manifest.json` y `evidence.json` | Presentes y verificados dentro del flujo | Presentes y verificados dentro del flujo |

Los seis hashes SHA-256 de los tres artefactos por volumen fueron contrastados por el verificador. El informe no reproduce hashes individuales que no fueron conservados en las salidas finales de auditoría.

### 4.4 Evidencia de GitHub Actions en `main`

- **Ejecución:** [Xientia Editorial CI — run 41266841060](https://github.com/adlair/xientia-foundation/actions/runs/41266841060).
- **Evento:** `push` a `main`.
- **Commit:** `b631ac74de49a7cbc0d9999eb81d349bfa889df0`.
- **Estado final:** `completed / success`.
- **Pasos confirmados como `success`:** Checkout; Install editorial dependencies; Inspect environment; Validate editorial CI contract; Run editorial regression suite; **Build and verify consultation editions on main**.

El paso de construcción de consulta está condicionado a `push` sobre `refs/heads/main`; no se habilitaron releases institucionales ni carga de artefactos por el workflow auditado.

## 5. Matriz de conformidad

| Control | Evidencia | Resultado |
| --- | --- | --- |
| Base Git identificada y limpia | Clon y estado Git | PASS |
| Política `draft` / `consulta-no-adoptada` | Contrato y evidencias | PASS |
| Adopción institucional automática deshabilitada | Contrato y workflow | PASS |
| Pruebas de regresión local | 114/114 | PASS |
| Pruebas en Pull Requests | Workflow y PR integrados | PASS |
| Pruebas tras `push` en `main` | Run 41266841060 | PASS |
| Construcción de consultas en `main` | Paso específico en run 41266841060 | PASS |
| Verificación independiente de XV-001 y XEP-0000 | `verify_package()` | PASS |
| Publicación exclusiva / sin reemplazo | Pruebas R2-C y motor existente | PASS en escenarios ensayados |
| Concurrencia de dos publicadores | Prueba real con un ganador | PASS en escenarios ensayados |
| Limpieza ante excepción e interrupción gestionada | Pruebas automatizadas | PASS |
| Recuperación automática ante `SIGKILL` o caída del host | Fuera de alcance | NO CERTIFICADA |
| Durabilidad ante pérdida súbita de energía | Fuera de alcance | NO CERTIFICADA |
| XF-000 bajo esquema de evidencia R2 | No contemplado | FUERA DE ALCANCE |

## 6. Hallazgos y resolución

### F43-AUD-001 — Desalineación entre contrato y automatización de `main`

**Observación:** el contrato requería pruebas y construcción de consultas en `main`, mientras el workflow inicial solo respondía a `pull_request`.
**Acción:** PR #6 añadió `push` a `main`, ajustó la clave de concurrencia e incorporó construcción y verificación de XV-001/XEP-0000.
**Validación:** ejecución real de `push` en `main` con todos los pasos relevantes en `success`.
**Estado:** **CERRADO — PASS**.

### F43-AUD-002 — Caché Python detectada como árbol Git sucio

**Observación:** nueve archivos `.pyc` no registrados en dos directorios `__pycache__` provocaron `ValueError: Dirty repository rejected`.
**Causa:** ejecuciones sin `PYTHONDONTWRITEBYTECODE=1` generaron archivos locales; establecer esa variable posteriormente no elimina los ya existentes.
**Acción:** limpieza controlada de ambos directorios de caché en el clon y repetición de la publicación con `PYTHONDONTWRITEBYTECODE=1`.
**Validación:** árbol limpio y ambos paquetes publicados y verificados.
**Estado:** **CERRADO OPERATIVAMENTE**. No se declara una solución universal permanente para todos los modos de ejecución.

### F43-AUD-003 — Verificación final de trazabilidad de los paquetes

**Observación:** las primeras verificaciones quedaron bloqueadas por AUD-002; no existía `evidence.json` en los destinos.
**Acción:** repetir ambas publicaciones tras recuperar un árbol limpio y verificar con `verify_package()`.
**Validación:** XV-001 y XEP-0000 con integridad, estructura, procedencia y política documental conformes.
**Estado:** **CERRADO — PASS**.

## 7. Riesgos residuales y límites

1. **Terminaciones abruptas:** `SIGTERM` sin manejo, `SIGKILL` o caída del host pueden dejar staging temporal residual; la limpieza gestionada no equivale a recuperación automática.
2. **Durabilidad física:** la publicación exclusiva y atómicamente visible en un sistema de archivos compatible no demuestra persistencia completa frente a corte eléctrico.
3. **Concurrencia adversarial:** las pruebas confirman los escenarios ensayados, no todas las intercalaciones posibles ni aislamiento absoluto frente a modificaciones maliciosas.
4. **Higiene de ejecución Python:** deben evitarse archivos `.pyc` no registrados antes de una construcción que exija Git limpio; se recomienda estandarizar `PYTHONDONTWRITEBYTECODE=1` y verificar el árbol antes de publicar.
5. **Alcance documental:** XF-000 conserva el flujo anterior; no debe presentarse como cubierto por la evidencia R2 de XV-001/XEP-0000.
6. **Evaluación visual:** las comprobaciones automáticas de estructura y correspondencia no reemplazan la revisión visual/editorial humana antes de distribuir documentos.

Estos riesgos se aceptan **para el cierre del alcance técnico auditado**, no como certificación de ausencia de riesgos ni autorización para una distribución institucional.

## 8. Dictamen y transición

**DICTAMEN: GO — F4.3 técnicamente cerrada dentro del alcance definido.**

Fundamento: los PR #1–#6 están integrados; la regresión de 114 pruebas aprobó en el clon de auditoría; los paquetes de consulta XV-001 y XEP-0000 aprobaron la verificación independiente; la ejecución de `push` sobre `main` aprobó el contrato, la regresión y la construcción con verificación de evidencias.

**Autorización técnica propuesta:** iniciar planificación de F4.4 a partir de `b631ac74de49a7cbc0d9999eb81d349bfa889df0`, manteniendo controles de procedencia, separación entre publicación técnica e institucional, y los riesgos residuales anteriores en el registro de decisiones.

**No autorizado por este dictamen:** adopción institucional, cambio del estado `draft`, publicación institucional automática, ni modificación normativa de los documentos fundacionales.

## 9. Referencias y reproducibilidad

- [Repositorio Xientia Foundation](https://github.com/adlair/xientia-foundation)
- [PR #1](https://github.com/adlair/xientia-foundation/pull/1), [PR #2](https://github.com/adlair/xientia-foundation/pull/2), [PR #3](https://github.com/adlair/xientia-foundation/pull/3), [PR #4](https://github.com/adlair/xientia-foundation/pull/4), [PR #5](https://github.com/adlair/xientia-foundation/pull/5), [PR #6](https://github.com/adlair/xientia-foundation/pull/6)
- [GitHub Actions — validación final de `main`](https://github.com/adlair/xientia-foundation/actions/runs/41266841060)
- Contrato: `tools/editorial/ci/editorial_ci_contract.json`
- Workflow: `.github/workflows/editorial-ci.yml`
- Pruebas: `tools/editorial/tests/`

**Control del documento:** este archivo es un informe preparado a partir de las evidencias indicadas. No se afirma que haya sido incorporado al repositorio, revisado por terceros o firmado institucionalmente. Su integración en Git deberá realizarse mediante un cambio separado y revisión correspondiente.
