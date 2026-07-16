# Constitución del Proyecto — PastryStock Manager

> **Artefacto SDD:** Gobernanza (nivel 0). Documento fundacional que fija los principios
> no negociables del proyecto. Todo `spec`, `plan`, `tarea` y línea de código debe poder
> justificarse contra este documento. Formaliza y eleva a rango normativo lo que estaba
> disperso en `CLAUDE.md`.

- **Proyecto:** PastryStock Manager — Sistema de gestión de inventario para pastelerías
- **Metodología rectora:** Spec-Driven Development (SDD) + Spec-Driven Testing (SDT)
- **Autor:** Franklin Figueroa Perez — UNSCH
- **Ventana de desarrollo:** 7–10 de julio de 2026
- **Estado:** Vigente

---

## Artículo I — Primacía de la especificación

1. **La especificación precede al código.** Ninguna funcionalidad se implementa sin una
   Historia de Usuario (HU) con escenarios de aceptación en formato BDD/Gherkin en
   `docs/user-stories.md`. El código es la *consecuencia* del spec, nunca su origen.
2. Todo cambio de comportamiento observable exige, en este orden: (a) actualizar el spec,
   (b) derivar o ajustar tareas en `04-tasks.md`, (c) escribir/ajustar la prueba, (d) implementar.
3. La trazabilidad HU → Tarea → Código → Prueba (`06-traceability.md`) es **obligatoria** y
   es la evidencia central de que el proyecto siguió SDD y no fue "código generado sin gobierno".

## Artículo II — Ciclo de vida obligatorio

El desarrollo recorre las cuatro fases clásicas del ciclo de vida del software, cada una con
su artefacto de evidencia:

| Fase | Artefacto de evidencia |
|---|---|
| **Análisis** | `01-analisis.md` (problema, alcance, requisitos F/NF, riesgos) |
| **Diseño** | `03-plan.md`, `architecture.md`, `database-schema.md` |
| **Pruebas** | `test-matrix.md` + suite en `backend/tests/` |
| **Despliegue** | `05-deployment.md` + `docker-compose*.yml` |

Ninguna fase posterior se da por cerrada si la anterior no tiene su artefacto actualizado.

## Artículo III — Arquitectura limpia y SOLID (no negociable)

1. Dependencia siempre hacia adentro: `api → application → domain ← infrastructure`.
2. La capa `domain/` no importa NADA externo (ni FastAPI, ni SQLAlchemy, ni Redis).
3. Los servicios reciben **interfaces (`Protocol`)**, nunca implementaciones concretas (DIP).
4. Las excepciones de negocio viven en `domain/exceptions.py`; jamás se lanza `HTTPException`
   desde un servicio. El mapeo a HTTP ocurre solo en la capa `api/`.

## Artículo IV — Invariantes de negocio (constraints de dominio)

Estas reglas se defienden en **doble capa** (validación de dominio + constraint en PostgreSQL):

1. `LocationCode` cumple `^(EST|REF|FRZ|CAB|CON|ALM)-\d{2}(-F\d{1,2})?$`. Solo `EST` admite
   sufijo de fila `-FX`.
2. **`movement_history` es INMUTABLE:** sin `updated_at`, FK con `ondelete=RESTRICT`. Las
   correcciones se hacen con nuevos movimientos de tipo `ADJUSTMENT`, nunca editando el pasado.
3. El stock **nunca** es negativo: constraint en BD + validación en `SupplyService`.
4. RBAC: `STAFF` solo registra `EXIT` y `WASTE`. `ENTRY` y `ADJUSTMENT` son ADMIN+.
5. Categorías: **cache-first** — Redis se consulta antes que PostgreSQL, con PostgreSQL como
   respaldo (modo degradado si Redis cae).

## Artículo V — Calidad y pruebas (SDT)

1. TDD por capas: prueba unitaria de dominio/servicio primero, luego integración.
2. Cobertura mínima exigida: **80 %** (`--cov-fail-under=80`).
3. Toda HU crítica tiene al menos un caso en `test-matrix.md` con su ID trazable (`TC-*`).
4. Los tests de integración usan una BD aislada (`pastry_test`), nunca la BD de desarrollo.

## Artículo VI — Convenciones de código

1. Sin comentarios obvios. Se comenta el **porqué**, no el qué.
2. `async/await` en toda la capa de acceso a datos.
3. Código nuevo imita el estilo circundante (nombres, densidad de comentarios, idioma).
4. Secretos y parámetros de entorno solo vía `.env` (ver `.env.example`); nunca hardcodeados.

## Artículo VII — Documentación como parte del entregable

1. Cada sesión de trabajo relevante se registra en la wiki (`docs/wiki/`) vía la skill `llm-wiki`.
2. Los artefactos de `docs/spec/` son parte del entregable evaluable, no documentación opcional.

---

### Procedimiento de enmienda

Cualquier cambio a esta constitución exige: justificación escrita en el commit, actualización
de los artefactos SDD afectados y verificación de que la matriz de trazabilidad sigue cerrada.
