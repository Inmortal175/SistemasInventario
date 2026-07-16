---
title: "Listados paginados cache-first con Redis"
tags: [cache, redis, paginacion, rendimiento]
source_count: 1
---

# Listados paginados cache-first con Redis

## Definición
Estrategia de lectura donde los listados paginados se sirven primero desde Redis y solo
consultan PostgreSQL si hay miss; las mutaciones invalidan el caché (HU-06).

## Implementación
- Clave por parámetros: `supplies:page:{page}:{limit}:cat:{cat}:loc:{loc}`.
- `offset = (page - 1) × limit`.
- `SupplyService.list_active` devuelve `(respuesta, cache_status)`; el endpoint expone el
  header `X-Cache: HIT|MISS`.
- Invalidación: `create` de insumo, cada movimiento, conciliación y producción borran
  todas las páginas cacheadas con `scan_iter(match="supplies:page:*")`.

## Fuentes que lo mencionan
- [[fuentes/sesion-backend-completo-16-hu]] — verificado: MISS luego HIT en 2ª lectura
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — caché de `settings:system`

## Perspectivas/decisiones
Mismo patrón cache-first que ya usaban las categorías (índice `categories:active:all` y
set de nombres). Los KPIs del dashboard usan cache-first con TTL corto (30s). Los ajustes
del sistema añadieron `settings:system` ([[conceptos/configuracion-sistema-en-bd]]), que se
lee en cada render del layout raíz.

La capa de interfaz que consume esta paginación está en
[[conceptos/paginacion-ui-searchparams]].

**Deuda saldada (2026-07-15):** el frontend `getSupply(id)` traía la página con `limit:100` y
filtraba en memoria porque no existía un endpoint de detalle. Se añadió `GET /supplies/{id}`
(`SupplyService.get_detail`, sin caché, 404 vía `ItemNotFoundError`) y `getSupply` ahora
llama directo a `/supplies/{id}`. La ficha resuelve por id sin depender del tamaño del listado.

## Contradicciones detectadas
Ninguna, pero hay un **riesgo abierto**: solo `settings:system` tolera una entrada escrita
por una versión anterior del schema. `supplies:page:*`, `categories:active:all` y
`dashboard:kpis` alimentan constructores de Pydantic sin protección, así que un despliegue
que les añada campos obligatorios devolverá 500 hasta que la caché expire. Ver
[[conceptos/cache-obsoleta-tras-cambio-de-schema]].
