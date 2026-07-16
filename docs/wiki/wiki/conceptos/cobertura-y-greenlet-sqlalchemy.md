---
title: "Cobertura subestimada: coverage.py y el greenlet de SQLAlchemy async"
tags: [testing, cobertura, sqlalchemy, greenlet, pytest, herramientas]
source_count: 1
---

# Cobertura subestimada: coverage.py y el greenlet de SQLAlchemy async

## Definición
`coverage.py` **deja de registrar líneas** en cuanto el código entra en un greenlet distinto
al principal. SQLAlchemy async ejecuta el driver dentro de un greenlet (`greenlet_spawn`),
así que todo lo que un servicio hace **después de su primer `await` contra la base** se
reporta como no ejecutado, aunque el test pase.

## Cómo se detectó
`pytest tests/integration` fallaba el umbral con **77.50 %**, mientras la suite completa daba
82.61 %. El síntoma que delató la causa: `test_production_simulate_and_produce` pasaba (el
endpoint devolvía 200 y `feasible: true`), pero `production_service.py` figuraba al **41 %**
con `simulate()` y `produce()` marcadas como no ejecutadas — algo imposible.

La pista definitiva estaba en `create_recipe`:

```
41%   61-68, 71-73, 88-109, 134-169, ...
```

La línea 55 (`recipe = await self._recipes.create(...)`) sí aparecía cubierta; la 61 (el
`for` que sigue) no. La cobertura moría exactamente en el primer `await` a la base. Los
tests **unitarios** de ese mismo servicio, que usan `AsyncMock` y nunca tocan SQLAlchemy,
lo cubrían al 72 %.

## Solución
```toml
# backend/pyproject.toml
[tool.coverage.run]
source = ["app"]
concurrency = ["thread", "greenlet"]
```

Un solo test de producción pasó de 41 % a 75 % en ese archivo. Sin escribir un test nuevo:

| Suite | Antes | Después |
|---|---|---|
| Solo integración | 77.50 % | **87.69 %** |
| Completa (119 tests) | 82.61 % | **88.57 %** |

## Regla asociada: exclusión de los Protocol
```toml
[tool.coverage.report]
exclude_also = ["class .*\\(Protocol\\):"]
```
Las interfaces de repositorio (DIP) son firmas de tipo con cuerpo `...`; nunca se ejecutan.
Cuidado: una regla `^\s*\.\.\.$` **no funciona** aquí, porque el `...` va en la misma línea
que el `def`. Hay que excluir la línea de la clase, que arrastra todo su cuerpo.

## Fuentes que lo mencionan
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — sesión donde se diagnosticó

## Perspectivas/decisiones
El umbral `--cov-fail-under=80` vive en `addopts`, así que **se aplica a cualquier subconjunto
que corras**. Correr solo un directorio de tests siempre reportará menos cobertura que la
suite entera. Eso es esperable y no es un bug; el bug era el greenlet.

Se descartó relajar el umbral o moverlo fuera de `addopts`: el número era falso, no el umbral.

## Gaps reales que quedan
Tras la corrección, lo genuinamente no cubierto por integración es:
`api/v1/endpoints/websocket.py` (38 líneas) y `infrastructure/cache/pubsub_listener.py`
(26 líneas) — el canal WebSocket y el retransmisor de Pub/Sub no tienen tests de
integración. Ver [[conceptos/websockets-redis-pubsub]].

## Contradicciones detectadas
Las cifras de cobertura anteriores a 2026-07-09 registradas en esta wiki (81.8 %, 82.6 %)
**subestimaban** la cobertura real por esta causa.
