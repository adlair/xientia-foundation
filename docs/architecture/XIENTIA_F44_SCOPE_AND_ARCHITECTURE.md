# Xientia Foundation — Alcance y arquitectura técnica F4.4

**Identificador:** XIENTIA-F44-SCOPE-ARCHITECTURE
**Versión:** 0.1 — propuesta para revisión
**Fecha:** 31 de octubre de 2026 (México)
**Repositorio:** `adlair/xientia-foundation`
**Línea base:** `8977494c360fa448e242262d41728af8f7b8352c` (integración del acta F4.3)
**Estado:** Diseño preliminar; sin autorización de implementación ni adopción institucional

## 1. Propósito

F4.3 dejó funcionando la construcción editorial validada, la generación de evidencias y la publicación exclusiva de paquetes de consulta. El cierre técnico quedó documentado en `docs/audits/XIENTIA_F43_TECHNICAL_CLOSURE_AUDIT.md`. F4.4 debe atender las limitaciones operativas que permanecieron abiertas, sin rehacer el motor que ya fue probado.

El propósito de esta fase es que una publicación pueda reconstruirse bajo condiciones conocidas, identificarse después de una interrupción, verificarse en el tiempo y auditarse sin depender de una sesión de desarrollo particular. Se mantendrá la distinción entre **publicación técnica de un paquete de consulta** y **distribución o adopción institucional**. La segunda no forma parte de F4.4.

## 2. Punto de partida y restricciones

La base disponible incluye `build_library.py`, `render_library.py`, `validated_publish.py`, `atomic_publish.py`, los perfiles de volumen y los módulos `evidence_schema.py`, `evidence_verify.py` y `evidence_generate.py`. El workflow `.github/workflows/editorial-ci.yml` ejecuta regresiones en Pull Requests y, en `main`, construye y verifica XV-001 y XEP-0000. El acta F4.3 registra 114 pruebas locales aprobadas y la ejecución de CI correspondiente a su cierre.

Las siguientes condiciones no se negociarán durante F4.4:

- Las fuentes Markdown y su procedencia Git seguirán siendo la referencia editorial.
- Los paquetes con evidencias de F4.3 seguirán limitados a XV-001 y XEP-0000, salvo decisión y pruebas expresas de ampliación. XF-000 conserva su tratamiento anterior.
- Los documentos seguirán en `draft`, edición `consulta-no-adoptada`, con `institutional_adoption: false`.
- No se introducirán aprobaciones, releases institucionales ni modificaciones normativas automáticas.
- Los cambios deberán ser compatibles con la interfaz y las pruebas existentes; cualquier ruptura requerirá una decisión documentada.
- Las herramientas de auditoría no modificarán fuentes ni paquetes ya publicados.

## 3. Alcance de trabajo

### R1. Entorno y reproducibilidad

Se levantará un inventario de las versiones y condiciones que influyen en el resultado editorial: Python, LibreOffice, Pandoc, PyMuPDF, paquetes de sistema, fuentes tipográficas, configuración regional, zona horaria y parámetros de conversión. Se definirá un perfil de construcción versionado y una forma de registrar diferencias entre ejecuciones.

No se asumirá que dos ODT o PDF serán idénticos byte a byte. Se distinguirán tres niveles: **igualdad de fuentes**, **equivalencia de contenido y estructura** e **igualdad binaria**. Esta última solo podrá exigirse después de identificar y controlar los metadatos variables.

**Aceptación R1:** dos construcciones independientes desde el mismo commit producen resultados equivalentes conforme a reglas documentadas; toda diferencia observada se clasifica y queda asociada a la versión del entorno. La ejecución no genera archivos `.pyc` no registrados dentro del árbol auditado.

### R2. Recuperación y manejo de staging

El publicador actual utiliza staging temporal y publicación exclusiva del directorio. F4.4 añadirá un procedimiento conservador para identificar residuos después de terminaciones abruptas. Cada área temporal gestionada deberá tener identidad de ejecución, propietario, destino previsto y estado verificable.

La recuperación tendrá dos pasos separados: **inspeccionar** y **actuar**. Por defecto solo se permitirá inspección. Una limpieza deberá exigir confirmación explícita, demostrar que el directorio pertenece al proceso editorial y descartar actividad vigente. Un PID aislado no será prueba suficiente de propiedad, porque puede reutilizarse.

**Aceptación R2:** una interrupción simulada no deja un paquete final parcial; los residuos se detectan y describen sin borrar rutas ajenas. Las pruebas de limpieza deben cubrir rutas manipuladas, enlaces simbólicos, procesos concurrentes y ejecuciones aún activas. No se promete recuperación automática ante pérdida de energía.

### R3. Inventario y cadena de custodia

Se definirá un inventario externo a los paquetes publicados. Cada entrada identificará volumen, commit, hashes, versión de herramientas, momento de registro, resultado de verificación y ubicación del paquete. Los registros históricos serán inmutables en el flujo normal; una corrección generará un evento nuevo que haga referencia al anterior.

El inventario no sustituirá `manifest.json` ni `evidence.json`. Su función será permitir consultas y detectar cambios posteriores, manteniendo el paquete como unidad autónoma de verificación.

**Aceptación R3:** un tercero puede reconstruir la relación entre fuente, construcción, evidencia y paquete; cualquier modificación de un artefacto se detecta y se registra como fallo sin reescribir la evidencia original. Se documentarán expresamente los límites de confianza del inventario local.

### R4. Auditoría continua

Se añadirá una operación de auditoría de solo lectura, ejecutable manualmente y desde CI. La periodicidad se decidirá después de medir duración y consumo. El informe deberá distinguir entre controles aprobados, fallidos, no ejecutados y fuera de alcance; una ausencia de evidencia nunca contará como PASS.

La automatización no distribuirá documentos, no creará releases y conservará permisos mínimos. Se separarán los informes de ejecución de cualquier publicación de consulta.

**Aceptación R4:** la auditoría reproduce la verificación de paquetes existentes y produce un resumen verificable; las fallas provocan un estado de salida no exitoso. Las ejecuciones de PR y `main` mantienen sus garantías actuales.

### R5. Auditoría independiente y cierre

Se ejecutarán las pruebas desde un clon limpio, se revisarán los cambios contra los contratos, se probarán fallos e interrupciones y se documentarán los riesgos no resueltos. El cierre requerirá un acta separada, integrada por Pull Request, y una decisión GO, GO condicionado o NO-GO.

**Aceptación R5:** matriz de requisitos y evidencias completa, pruebas reproducibles, hallazgos con responsable y resolución, y ausencia de adopción institucional implícita.

## 4. Arquitectura lógica

```text
Fuentes Markdown + perfiles + contrato + commit Git
                         |
                         v
             Perfil de construcción F4.4 (R1)
                         |
                         v
         Motor editorial existente F4.3
      build -> render -> validate -> evidence
                         |
                         v
          Staging privado identificado (R2)
                         |
                  validación final
                         |
                         v
        Publicación exclusiva del directorio
                         |
             +-----------+-----------+
             |                       |
             v                       v
     Paquete verificable      Inventario externo (R3)
     MD / ODT / PDF           y eventos de auditoría
     manifest / evidence              |
                                     v
                         Auditoría de solo lectura (R4)
                                     |
                                     v
                           Informe y cierre (R5)
```

### Responsabilidades

| Componente | Responsabilidad | Regla de integración |
| --- | --- | --- |
| Motor F4.3 | Construir, convertir y validar documentos | Se reutiliza; cambios mínimos y justificados |
| Perfil R1 | Registrar condiciones de construcción | Versionado, sin sobrescribir el contrato editorial |
| Gestor R2 | Identificar staging y orientar recuperación | Sin borrado automático de rutas ambiguas |
| Inventario R3 | Referenciar paquetes y registrar eventos | Separado de `manifest.json` y `evidence.json` |
| Auditor R4 | Comprobar integridad y emitir resultados | Solo lectura respecto de fuentes y paquetes |
| CI | Ejecutar regresión y controles definidos | Sin permisos de escritura ni releases institucionales |

## 5. Contratos e invariantes

**C1. Identidad de fuente.** Cada paquete verificable remite a un commit Git concreto. El árbol de fuentes deberá estar limpio según la política aplicable antes de generar evidencias.

**C2. Integridad.** Los hashes se calculan sobre bytes reales; una discrepancia produce rechazo. Las comparaciones estructurales no reemplazan los hashes ni la revisión visual.

**C3. Publicación exclusiva.** El destino no se sobrescribe. La operación atómica protege la visibilidad del directorio en sistemas de archivos compatibles; no certifica por sí sola durabilidad ante corte eléctrico.

**C4. Recuperación conservadora.** No se borran directorios por coincidencia de nombre o antigüedad únicamente. Debe verificarse propiedad, ausencia de actividad y confinamiento de rutas antes de cualquier limpieza.

**C5. Evidencia inmutable.** Un paquete publicado no se reescribe para actualizar el inventario. Los resultados posteriores se agregan como registros independientes.

**C6. Separación institucional.** Ningún éxito de CI, firma técnica o evento de inventario equivale a ratificación o adopción institucional.

**C7. Fallo explícito.** Las herramientas deben distinguir PASS, FAIL, NOT VERIFIED y OUT OF SCOPE. Una excepción inesperada no se convierte en aprobación.

## 6. Modelo inicial de datos

El diseño definitivo del inventario se establecerá en R3. Como referencia, cada entrada deberá contemplar:

| Campo | Finalidad |
| --- | --- |
| `record_id` | Identificador único del registro |
| `package_id` | Identidad lógica del paquete |
| `volume` | XV-001 o XEP-0000, según contrato vigente |
| `git_commit` | Commit de procedencia |
| `artifact_hashes` | Hashes de los archivos verificados |
| `manifest_hash` / `evidence_hash` | Integridad de metadatos del paquete |
| `toolchain_profile` | Referencia al entorno de construcción |
| `verification_result` | PASS, FAIL o NOT VERIFIED |
| `recorded_at` | Momento del registro con zona horaria explícita |
| `previous_record_id` | Vínculo opcional a evento anterior |

No se selecciona todavía SQLite, PostgreSQL ni otro mecanismo persistente. La elección dependerá del modelo de concurrencia, portabilidad y necesidades de auditoría identificadas en R3.

## 7. Seguridad y pruebas

La matriz mínima incluirá pruebas positivas y negativas para: cambios en fuentes, manifiestos o evidencias; rutas fuera del directorio permitido; enlaces simbólicos; destinos preexistentes; dos publicadores simultáneos; fallos antes y después de la publicación; interrupciones gestionadas y abruptas; residuos de staging; diferencias entre versiones de herramientas; y ausencia de permisos de publicación institucional.

La ejecución de pruebas destructivas utilizará directorios temporales propios. No se emplearán rutas reales de usuario como objetivos de limpieza. Las pruebas que dependan de Linux o de una operación específica del sistema de archivos se identificarán como tales.

El conjunto de 114 pruebas de F4.3 constituye la referencia histórica, no una cifra de aceptación fija: F4.4 deberá conservarlas y añadir las que correspondan a cada incremento.

## 8. Secuencia y puntos de control

| Incremento | Entregable | Condición para avanzar | Estimación inicial |
| --- | --- | --- | --- |
| R1 | Perfil de entorno e informe de reproducibilidad | Dos construcciones comparadas y diferencias clasificadas | 2 semanas |
| R2 | Procedimiento y herramientas de recuperación | Pruebas de propiedad, confinamiento e interrupción | 3 semanas |
| R3 | Esquema e inventario de custodia | Trazabilidad completa y detección de alteraciones | 3 semanas |
| R4 | Auditoría continua y CI | Ejecución verificable sin distribución institucional | 2 semanas |
| R5 | Auditoría y acta de cierre | Dictamen sustentado en evidencias | 1 semana |

**Estimación total preliminar:** 11 semanas de trabajo secuencial. No es una fecha comprometida; se revisará después del inventario y las mediciones de R1.

Cada incremento deberá desarrollarse en una rama aislada, pasar sus pruebas locales y CI, someterse a revisión y fusionarse mediante Pull Request. La aprobación de un incremento no implica aprobación automática del siguiente.

## 9. Exclusiones y asuntos por decidir

Quedan fuera de F4.4: adopción o ratificación institucional, votaciones, administración de miembros, distribución pública automática, interfaz web general, migración a microservicios y rediseño del contenido fundacional.

Antes de iniciar R2 y R3 deberán resolverse, por escrito, las siguientes decisiones: política de retención de staging; límites de confianza del inventario; tratamiento de paquetes producidos por versiones anteriores; nivel de reproducibilidad exigible; y si una futura firma criptográfica aporta una garantía necesaria frente a las alternativas disponibles.

XF-000 no se incorporará al esquema de evidencias R2 por analogía. Requiere una decisión de alcance independiente.

## 10. Riesgos y seguimiento

| Riesgo | Prioridad | Respuesta prevista |
| --- | --- | --- |
| Borrado de recursos ajenos durante recuperación | Crítica | Inspección previa, prueba de propiedad y confirmación explícita |
| Evidencia inconsistente con el paquete | Alta | Verificación independiente y hashes |
| Cambios concurrentes o rutas manipuladas | Alta | Confinamiento, controles de rutas y pruebas adversariales |
| Variaciones entre entornos | Alta | Perfil de herramientas y comparación reproducible |
| Terminación abrupta | Alta | Identificación y recuperación conservadora de staging |
| Archivos `.pyc` en el repositorio | Media | Prevención explícita y verificación de árbol limpio |
| Diferencia entre contrato y CI | Media | Pruebas de conformidad del workflow |
| Confusión entre publicación técnica y adopción | Crítica | Estados documentales y permisos separados |

## 11. Criterio de aprobación de esta propuesta

La aprobación de esta versión 0.1 significa conformidad con el **alcance y la dirección arquitectónica**. No autoriza todavía cambios en el motor ni implica que se hayan ejecutado pruebas F4.4. Antes del primer commit de implementación se realizará un inventario de código, dependencias, contratos y pruebas de F4.3; con ese resultado se redactará el diseño detallado de R1.

**Decisión propuesta:** aprobar F4.4 v0.1 para planificación y comenzar el inventario técnico R1. Mantener el estado institucional de los documentos fundacionales sin cambios.

## 12. Referencias

- [Repositorio Xientia Foundation](https://github.com/adlair/xientia-foundation)
- [Acta de cierre técnico F4.3](https://github.com/adlair/xientia-foundation/blob/main/docs/audits/XIENTIA_F43_TECHNICAL_CLOSURE_AUDIT.md)
- [PR #5 — Publicación con evidencias](https://github.com/adlair/xientia-foundation/pull/5)
- [PR #6 — CI en main](https://github.com/adlair/xientia-foundation/pull/6)
- [PR #7 — Acta F4.3](https://github.com/adlair/xientia-foundation/pull/7)
- [GitHub Actions — ejecución validada de main en F4.3](https://github.com/adlair/xientia-foundation/actions/runs/41266841060)

---

**Control del documento:** propuesta de arquitectura para revisión técnica. No constituye una auditoría F4.4 ejecutada, una aprobación institucional ni una instrucción de publicación de documentos fundacionales.
