---
title: "Sesión: formalización de la evidencia SDD (Spec Kit)"
date: 2026-07-10
source_url: ""
source_path: ""
type: sesion
tags: [sdd, spec-kit, metodologia, documentacion, ciclo-de-vida, trazabilidad]
---

# Sesión: formalización de la evidencia SDD (Spec Kit)

## Resumen
El docente exige que el proyecto **evidencie la aplicación de Spec-Driven Development (SDD)**
a lo largo de todo el ciclo de vida (Análisis → Diseño → Pruebas → Despliegue) y no que sea
"solo una app hecha con IA". Se auditó el estado actual y se detectó que la evidencia SDD
existía pero estaba **incompleta y dispersa**: sólidos `user-stories.md` (16 HU / 35 escenarios
BDD), `architecture.md`, `database-schema.md` y `test-matrix.md`, pero **sin** documento de
análisis, **sin** descomposición en tareas, **sin** plan de despliegue formal y **sin** matriz
de trazabilidad. Ese último hueco —tareas + trazabilidad— es justo lo que distingue "SDD real"
de "código generado sin gobierno".

Se creó la carpeta `docs/spec/` con la cadena formal de artefactos siguiendo la estructura de
**Spec Kit** adaptada a Markdown manual (opción que el propio docente aceptó).

## Ideas clave
- La app ya estaba construida; se optó por **formalización honesta**: los documentos reflejan
  decisiones reales del proyecto, sin fabricar un cronograma día a día ficticio.
- El artefacto de mayor valor probatorio es la dupla **`04-tasks.md`** (71 tareas en 12 bloques,
  ordenadas, con dependencias, mapeadas a HU y a fase del ciclo) + **`06-traceability.md`**
  (matriz Requisito → HU → Tarea → Código → Prueba, cerrada para las 16 HU).
- Cada artefacto se ancla a una fase del ciclo de vida, de modo que la carpeta *es* la evidencia
  del recorrido Análisis→Diseño→Pruebas→Despliegue.
- Correcciones de fidelidad tras verificar el código: los seeds son
  `backend/scripts/seed_admin.py` y `seed_demo.py` (no `python -m app.seed`); el health check
  real es `GET /health` (definido en `app/main.py`).

## Artefactos creados (docs/spec/)
- `00-constitution.md` — gobernanza; formaliza y eleva a norma lo disperso en el `CLAUDE.md` raíz.
- `01-analisis.md` — problema, alcance, actores, 16 RF, 10 RNF, riesgos con mitigación.
- `02-specification.md` — índice maestro de las 16 HU (detalle canónico en `user-stories.md`).
- `03-plan.md` — diseño: stack, capas, decisiones D-01…D-11, contrato de API, caché, seguridad.
- `04-tasks.md` — descomposición en 71 tareas / 12 bloques, trazables a HU y fase.
- `05-deployment.md` — topología Docker, migraciones Alembic 001-006, checklist de verificación.
- `06-traceability.md` — matriz de trazabilidad cerrada + trazabilidad de reglas de negocio y fases.
- `README.md` — índice navegable y flujo SDD de la carpeta.

## Entidades mencionadas
- [[entidades/pastrystock-manager]] — proyecto sobre el que se formaliza la metodología

## Conceptos relacionados
- [[conceptos/spec-driven-development-spec-kit]] — metodología y su estructura de artefactos
- [[conceptos/rbac]] — regla de negocio trazada en la matriz
- [[conceptos/fifo-lotes-vencimiento]] — HU-13, trazada en la matriz
- [[conceptos/produccion-bom-transaccion-atomica]] — HU-15, trazada en la matriz

## Notas de síntesis
Pendiente único del plan de trabajo: `T-DOC-03` (informe de trabajo final), que consume el resto
de artefactos como anexos. La carpeta `docs/spec/` es ahora la fuente de evidencia SDD para la
sustentación y el informe.
