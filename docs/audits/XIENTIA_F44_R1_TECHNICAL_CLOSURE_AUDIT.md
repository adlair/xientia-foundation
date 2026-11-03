# Xientia — Acta de cierre técnico F4.4-R1

**Identificador:** XIENTIA-F44-R1-TECHNICAL-CLOSURE-AUDIT
**Versión:** 1.0 — propuesta de cierre para revisión
**Fecha:** 2 de noviembre de 2026 (México)
**Repositorio:** `adlair/xientia-foundation`
**Fase:** F4.4-R1 — Comparador de reproducibilidad editorial
**Línea base:** `05ee701ab3c3f8bb8d073073295256460bad861a`
**Dictamen:** **GO — cierre del alcance técnico implementado y verificado**, con limitaciones expresas.

## 1. Objeto y alcance

Esta acta documenta el cierre técnico del incremento F4.4-R1. Su propósito es dejar constancia de la incorporación de un comparador de reproducibilidad para paquetes editoriales de consulta de Xientia, de los controles asociados y de las evidencias disponibles al momento del cierre. No constituye aprobación institucional de los documentos, certificación general de seguridad ni garantía de igualdad binaria entre construcciones independientes.

El alcance se limita a la comparación de paquetes de **XV-001** y **XEP-0000**, previamente verificados mediante el mecanismo de evidencias de F4.3. Los documentos fuente Markdown, los validadores y contratos de F4.3, y la política de publicación institucional quedan fuera de las modificaciones de este incremento.

## 2. Línea base y trazabilidad

La implementación se integró mediante el [Pull Request #9](https://github.com/adlair/xientia-foundation/pull/9), titulado *feat: add F4.4 R1 editorial reproducibility comparator*. El commit de integración en `main` es `05ee701ab3c3f8bb8d073073295256460bad861a`; el último commit de la rama técnica es `6fb06b2150111ba763d140878403086cc52c75e6`.

La revisión del diferencial `main...HEAD`, realizada antes de la fusión, mostró cinco archivos nuevos y **1,202 líneas añadidas**, sin eliminaciones. La comprobación `git diff --check` no reportó problemas de formato. Después de la fusión se comprobó que `main` estaba actualizado, que el árbol Git estaba limpio y que los cinco archivos figuraban en el índice.

| Archivo incorporado | Responsabilidad |
| --- | --- |
| `tools/editorial/reproducibility_compare.py` | Verificación previa de paquetes y comparación L1–L4. |
| `tools/editorial/reproducibility_limits.py` | Política y validaciones de recursos para ZIP/ODT y PDF. |
| `tools/editorial/tests/test_reproducibility_compare.py` | Regresiones funcionales, visuales y controles de seguridad. |
| `tools/editorial/tests/test_reproducibility_integration.py` | Construcción y comparación de paquetes reales; procedencia Git. |
| `tools/editorial/tests/test_reproducibility_limits.py` | Pruebas de límites de tamaño, estructura y lectura. |

## 3. Arquitectura de comparación

El comparador verifica ambos paquetes mediante `verify_package()` antes de evaluar sus diferencias. Exige el mismo volumen y commit Git y comprueba nuevamente los hashes de los artefactos, manifiestos y evidencias al concluir la comparación. La relectura final detecta ciertas alteraciones ocurridas durante la operación; no constituye un bloqueo de archivos ni una instantánea transaccional.

| Nivel | Criterio de evaluación | Interpretación |
| --- | --- | --- |
| **L1 — Contenido** | Igualdad del Markdown y del texto extraído de cada página PDF. | Equivalencia de contenido conforme a las representaciones comparadas. |
| **L2 — ODT** | Comparación de componentes ZIP, atributos seleccionados y XML normalizado. | Equivalencia de los componentes examinados, con exclusión controlada de fechas volátiles. |
| **L3 — Presentación** | Renderizado PDF a 72 DPI, RGB, sin alfa, y comparación de píxeles por página. | Equivalencia visual bajo ese perfil de renderizado. |
| **L4 — Binario** | SHA-256 de Markdown, ODT y PDF originales. | Informe de identidad o diferencia binaria, independiente de L1–L3. |

La normalización de `meta.xml` admite exclusivamente variaciones en `meta:creation-date` y `dc:date`. Las fechas de entradas ZIP no determinan por sí solas un fallo de L2. En cambio, cambios en otros componentes o atributos comprobados deben reflejarse en el resultado. La comparación de píxeles L3 no demuestra equivalencia visual a todas las resoluciones ni en todos los visores.

**La aprobación de L1, L2 y L3 no implica aprobación de L4.** En las construcciones examinadas se observaron diferencias binarias de ODT/PDF asociadas, entre otros elementos, a metadatos temporales y campos internos de PDF, aunque el contenido textual y las páginas renderizadas coincidían.

## 4. Controles de integridad y seguridad

Se incorporaron y probaron controles para rechazar una raíz de paquete que sea enlace simbólico, declaraciones DTD en el XML de metadatos y entradas ZIP duplicadas. El analizador XML se configura sin resolución de entidades, sin carga de DTD y sin acceso a red. Las pruebas negativas incluyen entidades externas, DTD sin entidades y mutaciones de metadatos.

La prueba de integración requiere que el repositorio de origen esté limpio. Se verificó el rechazo de un origen con archivos no registrados. La construcción de consulta utiliza un clon de referencia y comprueba la correspondencia con el commit esperado.

La validación de evidencias de F4.3 continúa siendo una precondición: F4.4-R1 no sustituye ni debilita las reglas de integridad, procedencia y estado documental existentes.

## 5. Límites operativos

| Recurso | Límite configurado |
| --- | ---: |
| Tamaño ODT | 25 MiB |
| Entradas ZIP | 256 |
| Tamaño declarado por componente ZIP | 16 MiB |
| Total declarado descomprimido ZIP | 64 MiB |
| Tamaño PDF | 50 MiB |
| Páginas PDF | 500 |
| Píxeles por página a 72 DPI | 10,000,000 |

La comparación ODT revisa el inventario ZIP antes de leer componentes y utiliza lectura acotada, con comprobación de bytes obtenidos frente al tamaño declarado. Para PDF se comprueban tamaño, cantidad de páginas y dimensiones; el cálculo de píxeles utiliza redondeo hacia arriba para evitar subestimaciones. Los límites están respaldados por pruebas positivas y negativas.

Como referencia del inventario realizado durante R1, XV-001 produjo un ODT de 44,229 bytes y un PDF de 368,162 bytes, con 52 páginas; XEP-0000 produjo un ODT de 13,728 bytes y un PDF de 189,235 bytes, con 16 páginas. Ambos documentos usaron páginas de 612 × 792 puntos en la muestra examinada. Estos valores describen esas construcciones, no límites normativos para futuras ediciones.

## 6. Evidencias de validación

**Pruebas locales.** La suite editorial completa terminó con **140 pruebas aprobadas, cero fallos y cero errores**, en **45.153 segundos**, después del commit `6fb06b2`. La integración real específica de reproducibilidad terminó con **2/2 pruebas aprobadas**: rechazo de origen Git sucio y comparación de paquetes de consulta reales. Los árboles de trabajo y de referencia se comprobaron limpios.

**Integración continua.** El workflow *Xientia Editorial CI* del PR #9 terminó satisfactoriamente. Después de la fusión, la ejecución **#14**, asociada al commit `05ee701` sobre `main`, también mostró resultado satisfactorio en GitHub Actions (duración aproximada de **1 min 44 s** según el historial mostrado). Esta evidencia confirma el resultado global del workflow; el desglose individual de pruebas debe consultarse en los logs de la ejecución si se requiere una auditoría adicional.

**Integridad del alcance.** La comparación del PR registró cinco archivos nuevos exclusivamente bajo `tools/editorial/`. No se incorporaron modificaciones a textos fundacionales ni mecanismos de adopción institucional.

## 7. Hallazgos tratados

| Referencia | Hallazgo | Resultado |
| --- | --- | --- |
| F44-R1-AUD-001 | Asignaciones duplicadas de rutas de manifiesto y evidencia. | Duplicación eliminada. |
| F44-R1-AUD-002 | Comprobación de enlaces simbólicos de la raíz. | Rechazo explícito del enlace simbólico final, con prueba negativa. |
| F44-R1-AUD-003 | XML con DTD y entidades externas. | Rechazo de DTD antes de canonicalizar; pruebas negativas aprobadas. |
| F44-R1-AUD-004 | Origen Git sucio en integración. | Comprobación de limpieza y prueba negativa aprobadas. |

Estos resultados cierran los hallazgos dentro del alcance de las pruebas implementadas. No implican que todas las variantes de rutas, documentos maliciosos o carreras de archivos estén cubiertas.

## 8. Riesgos residuales y exclusiones

1. **Concurrencia:** las verificaciones de hash antes y después de la comparación no proporcionan aislamiento transaccional ni impiden modificaciones intermedias.
2. **Recursos:** los límites de tamaño y geometría reducen riesgos conocidos, pero no imponen por sí mismos cuotas completas de memoria, CPU o tiempo para las bibliotecas subyacentes.
3. **Equivalencia visual:** L3 solo evalúa páginas renderizadas a 72 DPI bajo la configuración definida; no prueba equivalencia universal de visualización, accesibilidad o semántica PDF.
4. **Reproducibilidad binaria:** L4 puede informar diferencias legítimas en archivos cuya representación textual o visual coincide; no se normalizan ni reescriben los originales para forzar igualdad.
5. **Alcance documental:** el incremento no autoriza publicación institucional, adopción normativa, distribución automática ni cambios de estado a documentos de consulta.
6. **Seguridad de rutas:** el rechazo de un enlace simbólico final no equivale a una defensa completa frente a enlaces en todos los componentes antecesores o a sustituciones concurrentes.

## 9. Dictamen y transición

**GO — cierre técnico de F4.4-R1**, respecto de la implementación, pruebas e integración verificadas en la línea base `05ee701ab3c3f8bb8d073073295256460bad861a`.

Se considera satisfecho el objetivo de incorporar un comparador de reproducibilidad editorial con cuatro niveles de evaluación, controles básicos de seguridad y recursos, trazabilidad Git y cobertura de regresión. Las limitaciones del apartado 8 permanecen explícitamente abiertas como restricciones de alcance, no como garantías implícitas.

La siguiente etapa, **F4.4-R2**, podrá abordar recuperación ante interrupciones, staging abandonado y controles de resiliencia operativa. Su diseño, implementación y aceptación deberán evaluarse por separado, sin modificar retroactivamente el dictamen de R1.

**Estado institucional:** los documentos XV-001 y XEP-0000 permanecen en condición `draft`, edición `consulta-no-adoptada`, con `institutional_adoption: false`.
