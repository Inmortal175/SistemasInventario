---
title: "Invalidar caché al sembrar/borrar directo en la DB"
tags: [redis, cache-first, seed, reset, invalidacion, operaciones]
source_count: 1
---

# Invalidar caché al sembrar/borrar directo en la DB

## Definición
La app sirve varios listados **cache-first**: consulta Redis primero y usa PostgreSQL solo como
fallback. Los scripts de mantenimiento (`seed_demo.py`, `reset_system.py`) escriben **directo en
PostgreSQL**, saltándose la capa de servicio que normalmente invalida la caché. Consecuencia: si
Redis ya tenía una respuesta cacheada (típicamente una lista vacía obtenida antes de sembrar),
la app la sigue sirviendo aunque la DB ya cambió. Toda escritura directa que salte el servicio
**debe invalidar las llaves cache-first afectadas**.

## Síntoma
"Corrí el seed y funcionó (imprimió el ✅), pero el frontend sigue vacío: sin categorías, sin
insumos, sin productos." La DB tiene los datos; Redis sirve lo viejo.

## Llaves cache-first afectadas
Definidas en `app/infrastructure/cache/cache_keys.py`:
- `categories:active:all` (índice completo) y `categories:names:active` (set de nombres)
- `category:*` (individuales)
- `supplies:page:*` (listados paginados de insumos)
- `dashboard:kpis` (KPIs del dashboard)
- `settings:system` (identidad visual)

## Decisión
- `seed_demo.py` invalida esas llaves al terminar (`_invalidate_cache`), quedando
  auto-suficiente: sembrar y ya se ve.
- `reset_system.py` purga las mismas llaves tras borrar.
- **Purga selectiva, no `FLUSHDB`**: se dejan intactos rate-limits de login
  (`login:rate_limit:*`), blacklists de tokens (`token:*`) y locks de stock (`lock:stock:*`),
  que no son datos de demo. Ver [[conceptos/rate-limiting-redis]] y [[conceptos/blacklist-jwt-redis]].

## Perspectivas/decisiones
Alternativa descartada: hacer que el seed pase por los servicios (que sí invalidan caché). Se
prefirió escritura directa por velocidad y para no arrastrar Redis, alertas y WebSockets a un
script batch — a cambio de invalidar la caché explícitamente al final.

## Contradicciones detectadas
Ninguna. Complementa a [[conceptos/cache-first-paginacion]] (el lado de lectura) y a
[[conceptos/cache-obsoleta-tras-cambio-de-schema]] (otra forma del mismo patrón: Redis miente
cuando la DB cambió por fuera del flujo normal).

## Fuentes que lo mencionan
- [[fuentes/sesion-reset-sistema-y-cache-first-seed]] — diagnóstico e implementación
