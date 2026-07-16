# docs/spec — Evidencia de Spec-Driven Development (SDD)

Esta carpeta contiene la **cadena formal de artefactos SDD** del proyecto PastryStock Manager,
siguiendo la estructura de **Spec Kit** adaptada a Markdown manual. Demuestra que el desarrollo
se ejecutó con planeación previa y **paso a paso a lo largo de todo el ciclo de vida del
software** (Análisis → Diseño → Pruebas → Despliegue), y no como código generado sin gobierno.

## Cómo leer esta carpeta (orden recomendado)

| # | Artefacto | Fase del ciclo de vida | Qué responde |
|---|---|---|---|
| 0 | [`00-constitution.md`](00-constitution.md) | Gobernanza | Principios no negociables del proyecto |
| 1 | [`01-analisis.md`](01-analisis.md) | **Análisis** | Qué problema, para quién, con qué requisitos y riesgos |
| 2 | [`02-specification.md`](02-specification.md) | Especificación | Índice maestro de las 16 HU (detalle en `../user-stories.md`) |
| 3 | [`03-plan.md`](03-plan.md) | **Diseño** | Stack, capas, contrato de API, decisiones técnicas |
| 4 | [`04-tasks.md`](04-tasks.md) | Plan de trabajo | Descomposición en 71 tareas ordenadas y trazables |
| 5 | [`05-deployment.md`](05-deployment.md) | **Despliegue** | Cómo se levanta y verifica el sistema |
| 6 | [`06-traceability.md`](06-traceability.md) | Cierre | Matriz Requisito → Tarea → Código → Prueba |

## Flujo SDD

```
Constitución ─┐
              ▼
   Análisis ──► Especificación ──► Diseño ──► Tareas ──► Implementación
      (01)          (02)           (03)       (04)      (código + Pruebas)
                                                              │
                                                              ▼
                                                        Despliegue (05)
                                                              │
                                                              ▼
                                                   Trazabilidad (06) ── cierra el ciclo
```

## Artefactos relacionados (fuera de esta carpeta)

- `../user-stories.md` — las 16 HU con sus 35 escenarios BDD/Gherkin (fuente canónica del spec).
- `../architecture.md` — diagramas de arquitectura y SOLID (parte de la fase de Diseño).
- `../database-schema.md` — modelo de datos y constraints (parte de la fase de Diseño).
- `../test-matrix.md` — matriz de casos de prueba (parte de la fase de Pruebas).
- `../wiki/` — segundo cerebro: bitácora de sesiones y conceptos técnicos del desarrollo.

## Regla de oro (Constitución, Art. I)

> La especificación precede al código. Todo cambio de comportamiento actualiza primero el spec,
> luego las tareas, luego la prueba, y por último la implementación — dejando la matriz de
> trazabilidad cerrada.
