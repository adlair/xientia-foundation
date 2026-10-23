# A6 — Evaluación preliminar de privacidad, identidad y confianza científica

**Proyecto:** Xientia — Biblioteca Fundacional
**Referencia:** XV-001, Capítulo VIII; XF-000; XEP-0000
**Estado:** Propuesta de evaluación, no aprobada
**Fecha:** 2026-10-23
**Alcance:** México como jurisdicción inicial; expansión internacional pendiente de estudio

## 1. Propósito y límites

Xientia pretende reducir la suplantación y las cuentas fraudulentas, facilitar la vinculación institucional y mostrar trayectorias académicas con evidencia de procedencia. Estos objetivos no requieren necesariamente que Xientia conserve copias de identificaciones oficiales o concentre todos los datos personales de sus participantes.

Este documento define hipótesis de diseño, riesgos y decisiones pendientes. No acredita cumplimiento normativo, no sustituye una evaluación de impacto ni constituye asesoría jurídica. Antes de operar tratamientos de datos o integraciones, deberán revisarse las disposiciones vigentes y las obligaciones que correspondan al responsable real del tratamiento.

## 2. Cuatro dimensiones independientes

1. **Control de cuenta:** confirmar que una persona controla el acceso a una cuenta y puede recuperarlo de forma segura.
2. **Identidad personal:** comprobar, con un grado de confianza declarado, que la cuenta corresponde a una persona determinada. La prueba de humanidad y la identificación civil no son equivalentes.
3. **Trayectoria y afiliación:** vincular credenciales, membresías, adscripciones y reconocimientos con emisores competentes y vigencia verificable.
4. **Evaluación científica:** valorar métodos, evidencia y contribuciones mediante procedimientos adecuados. No debe inferirse a partir de los tres niveles anteriores.

Los distintivos visibles deberán comunicar qué fue verificado, por quién, cuándo y con qué límites. Se evitará un único distintivo de «científico verificado» que sugiera validación integral.

## 3. Incorporación por invitación institucional

El piloto podrá utilizar invitaciones emitidas por sociedades o instituciones participantes, con vigencia limitada, un solo uso cuando corresponda, controles contra abuso y posibilidad de revocación.

La invitación acredita únicamente el vínculo o autorización que la institución pueda confirmar. No verifica automáticamente títulos, publicaciones, pertenencia actual a un organismo ni calidad científica.

Las instituciones deberán poder corregir o retirar una afirmación de afiliación sin borrar la identidad personal ni la historia legítima de contribuciones del usuario.

## 4. Alternativas de verificación

| Mecanismo | Posible utilidad | Límite o riesgo |
|---|---|---|
| Correo institucional confirmado | Control de un canal de contacto | No demuestra identidad civil ni vigencia de afiliación |
| Invitación firmada o administrada por institución | Incorporación y vínculo declarado | Depende de la calidad del padrón y del proceso institucional |
| ORCID mediante flujo oficial de autorización | Vincular identificador académico | No certifica automáticamente todos los datos del perfil |
| Credencial emitida por universidad o sociedad | Respaldar afirmación concreta | Exige verificar emisor, alcance y vigencia |
| Documento oficial mediante proveedor autorizado | Comprobación reforzada cuando sea necesaria | Mayor exposición de datos, costos, errores y requisitos legales |
| Verificación manual excepcional | Resolver casos ambiguos | Riesgo de discrecionalidad y acceso excesivo a documentos |

La elección deberá basarse en riesgo, necesidad, proporcionalidad, accesibilidad y evidencia de efectividad. Debe existir un mecanismo de revisión para falsos rechazos y errores.

## 5. CURP, RENAPO e INE

La CURP es un identificador personal, no una prueba suficiente de que quien la proporciona sea su titular. Su conocimiento no demuestra presencia humana ni autorización para usar una identidad.

No se presupone que RENAPO o INE proporcionen APIs públicas disponibles para Xientia. Cualquier integración deberá contar con una evaluación previa de disponibilidad real, fundamento, condiciones contractuales, seguridad, alcance y autorizaciones.

**Decisión preliminar:** no exigir CURP ni copia de credencial para votar como condición general de registro del piloto. Cualquier uso excepcional requerirá una justificación documentada y un procedimiento específico de retención y eliminación.

## 6. SNII, becas, convocatorias y SECIHTI

La pertenencia al SNII, las becas y otros reconocimientos deberán presentarse con estado y procedencia diferenciados: declarado, respaldado o confirmado por fuente autorizada.

La publicación de convocatorias oficiales no equivale a disponer de una integración con SECIHTI ni a poder reutilizar sin límites los datos de beneficiarios. Las recomendaciones de convocatorias deberán permitir corregir información de perfil y explicar los criterios de compatibilidad.

## 7. Minimización, retención y derechos

Se propone separar:

- **Datos de cuenta:** información mínima para acceso, seguridad y recuperación.
- **Perfil público:** información elegida por el usuario y condiciones visibles de verificación.
- **Evidencia de credenciales:** metadatos de emisor, alcance, fecha y referencia; conservar documentos solo si es imprescindible.
- **Registros de seguridad:** acceso restringido y plazos definidos.
- **Información especialmente delicada:** tratamiento excepcional sujeto a necesidad y análisis jurídico.

Se deberán definir avisos de privacidad, finalidades, bases y condiciones aplicables, mecanismos para ejercer derechos de protección de datos, periodos de conservación, procedimientos de rectificación y reglas para transferencias o encargados.

La eliminación de una cuenta no implicará necesariamente borrar publicaciones científicas ya difundidas cuando existan obligaciones legítimas de preservación; esta excepción deberá explicarse previamente y evaluarse caso por caso.

## 8. Amenazas y controles propuestos

| Riesgo | Medidas candidatas |
|---|---|
| Suplantación de identidad | Invitaciones controladas, autenticación fuerte, revisión de incidentes |
| Creación masiva de cuentas | Límites de registro, controles adaptativos, análisis de abuso |
| Robo de cuenta | MFA, sesiones revocables, recuperación segura |
| Credenciales académicas falsas | Verificación por emisor y registro de procedencia |
| Filtración de documentos | Evitar su conservación; cifrado y accesos restringidos cuando sean indispensables |
| Uso indebido de información pública | Limitación de finalidad, permisos y auditoría |
| Falsos positivos de fraude | Apelaciones, revisión humana y registros de decisión |
| Automatización legítima confundida con bots | Cuentas de servicio identificadas y políticas diferenciadas |

No se propone utilizar reconocimiento facial o biometría como requisito general. Su eventual uso exigiría evaluación independiente de necesidad, impacto y alternativas.

## 9. Matriz inicial de decisiones para el MIV

| Decisión | Propuesta inicial | Estado |
|---|---|---|
| Registro inicial | Invitación institucional | Por validar |
| Identificador académico | Vinculación ORCID opcional | Por validar |
| Identidad civil obligatoria | No, por defecto | Propuesta |
| Credenciales | Declaradas con procedencia y verificación gradual | Por validar |
| CURP/INE/RENAPO | Sin integración en el MIV | Propuesta |
| SNII y becas | Campos declarativos diferenciados de datos confirmados | Por validar |
| Cuentas de automatización | Separadas de cuentas personales | Propuesta |
| Documentos oficiales | No retener por defecto | Propuesta |
| Eliminación, rectificación y apelación | Diseñar antes del piloto | Pendiente |

## 10. Validación jurídica y operativa necesaria

Antes del piloto deberán identificarse el responsable y los posibles encargados del tratamiento, el marco mexicano aplicable según su naturaleza, los flujos de datos, la ubicación de infraestructura, las transferencias, las finalidades, los periodos de retención y los contratos necesarios.

La revisión deberá contemplar, según corresponda, la legislación mexicana vigente sobre protección de datos personales en posesión de particulares o sujetos obligados, así como normas sobre identidad, propiedad intelectual y derechos de usuarios. La aplicabilidad y vigencia deben ser confirmadas por asesoría jurídica competente; no se presupone un único régimen para todas las instituciones participantes.

Se recomienda elaborar un mapa de datos y una evaluación de impacto en privacidad y seguridad antes de tratar información documental sensible o automatizar decisiones de verificación.

## 11. Pruebas y criterios de observación

El piloto deberá registrar, con datos agregados y protección adecuada, tasas de incorporación, errores de verificación, reclamaciones, tiempos de resolución, abandono del registro y carga administrativa para instituciones.

Las pruebas deberán incluir casos de cambio de afiliación, investigadores independientes, pérdida de acceso institucional, homónimos, datos erróneos y cuentas comprometidas.

Ninguna métrica de éxito debe basarse únicamente en el porcentaje de cuentas etiquetadas como verificadas.

## 12. Recomendación de cierre

Mantener XV-001 y el presente análisis en estado `draft`. Incorporar las decisiones de arquitectura, flujos y controles concretos a XA-002, XT-003 y XP-004. No anunciar verificación gubernamental, certificación de científicos ni cumplimiento normativo hasta contar con acuerdos, pruebas y revisión jurídica documentada.
