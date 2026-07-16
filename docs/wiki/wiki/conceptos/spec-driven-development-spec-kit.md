---
title: "Spec-Driven Development (SDD) y Spec Kit"
tags: [sdd, spec-kit, metodologia, ciclo-de-vida, trazabilidad, documentacion]
source_count: 1
---

# Spec-Driven Development (SDD) y Spec Kit

## Definición
**Spec-Driven Development (SDD)** es una metodología donde la **especificación precede al
código**: se planifica en detalle (tareas, alcance, pasos) antes de desarrollar, y el desarrollo
recorre todo el ciclo de vida del software (Análisis → Diseño → Pruebas → Despliegue). El código
es la *consecuencia* del spec, nunca su origen. Lo que distingue SDD de "código generado con IA
sin gobierno" es la **trazabilidad**: cada requisito se puede seguir hasta su tarea, su código y
su prueba.

**Spec Kit** es una de las herramientas/plantillas que materializan SDD (junto a Open Spec, Kiro,
o simplemente archivos `.md` de configuración manual). Define una cadena de artefactos:
`constitution → spec → plan → tasks → implementación`.

## Estructura adoptada en el proyecto (docs/spec/)
| Artefacto | Fase del ciclo de vida | Rol |
|---|---|---|
| `00-constitution.md` | Gobernanza | Principios no negociables |
| `01-analisis.md` | Análisis | Problema, alcance, RF/RNF, riesgos |
| `02-specification.md` | Especificación | Índice de HU (detalle en `user-stories.md`) |
| `03-plan.md` | Diseño | Stack, capas, decisiones, contrato API |
| `04-tasks.md` | Plan de trabajo | Descomposición en tareas trazables |
| `05-deployment.md` | Despliegue | Topología, migraciones, checklist |
| `06-traceability.md` | Cierre | Matriz Requisito→Tarea→Código→Prueba |

## Perspectivas/decisiones
- **Formalización honesta**: cuando la app ya existe, los artefactos SDD se redactan reflejando
  las decisiones reales, sin inventar cronogramas ficticios. La legitimidad viene de que el spec
  (`user-stories.md`) sí dirigió el desarrollo y de que la matriz de trazabilidad cierra.
- **El corazón de la evidencia** es `tasks.md` + `traceability.md`: sin descomposición en tareas
  ni matriz, un proyecto "parece" hecho con IA aunque tenga buenos specs.
- **Doble anclaje**: cada tarea se etiqueta con su HU *y* su fase del ciclo de vida, de modo que
  la documentación demuestra el recorrido completo del ciclo.
- El docente acepta explícitamente la variante **manual en `.md`** frente a herramientas dedicadas.

## Fuentes que lo mencionan
- [[fuentes/sesion-formalizacion-sdd-spec-kit]] — creación de la carpeta `docs/spec/`

## Contradicciones detectadas
Ninguna. Complementa la metodología ya declarada en [[entidades/pastrystock-manager]]
(SDD + TDD + SOLID) dándole soporte documental verificable.
