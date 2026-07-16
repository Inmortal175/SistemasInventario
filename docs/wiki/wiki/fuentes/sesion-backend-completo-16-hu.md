---
title: "Sesión: Completado del backend — 16 historias de usuario"
date: 2026-07-08
source_url: ""
source_path: ""
type: sesion-desarrollo
tags: [backend, fastapi, fifo, produccion-bom, rbac, websockets, redis, olap, testing]
---

# Sesión: Completado del backend — 16 historias de usuario

## Resumen
Sesión de desarrollo que completó el backend de PastryStock Manager cubriendo las 16
historias de usuario de `docs/user-stories.md`. Sobre una base que ya tenía HU-01 a
HU-07/09/11 parciales, se implementaron las HUs faltantes respetando la arquitectura
limpia por capas (domain → infrastructure → application → api) y el patrón de inyección
de dependencias vía providers. Se añadió la migración Alembic 002 (lotes, recetas,
columnas de costo y trazabilidad), 6 nuevos servicios, 6 nuevos routers y 4 archivos de
tests. Verificación end-to-end contra el stack Docker real (Postgres 16 + Redis 7).

## Ideas clave
- **Migración única 002** para todo lo nuevo: tablas `supply_batches`, `recipes`,
  `recipe_items`; columnas `locations.created_by` y `movement_history.unit_cost`.
- **FIFO por vencimiento** (HU-13): el consumo descuenta lotes ordenados por
  `expiration_date` (nulls last), con `SELECT ... FOR UPDATE` para atomicidad, y
  registra un único movimiento con desglose por lote en las notas.
- **Producción BOM** (HU-15) en dos fases: validación total de TODOS los ingredientes
  antes de descontar → si uno falla, `RecipeProductionShortageError` (422) y el
  dependency de sesión hace ROLLBACK, sin descontar ningún insumo.
- **RBAC estricto** por endpoint con `require_roles`: SUPERADMIN para gestión de
  usuarios (HU-10), ADMIN+ para conciliación/reportes/lotes, STAFF+ para consumo y
  producción.
- **Alertas en tiempo real** (HU-14): el servicio publica en canales Redis Pub/Sub
  (`alerts:low_stock`, `alerts:expiration_critical`); un listener en background
  (lifespan) retransmite a las conexiones WebSocket del grupo de administradores.
- **Corrección de spec**: el login devolvía 403 para credenciales inválidas; se creó
  `InvalidCredentialsError` → 401 para cumplir SC-HU04-02.

## Verificación realizada (end-to-end, stack Docker real)
- FIFO: EXIT de 15 L sobre lotes [A:10, B:20] → A agotado, B=15. ✔ (SC-HU13-02)
- Conciliación: físico 12 sobre 15 → Δ=-3, `ADJUSTMENT_SUB` trazable. ✔ (SC-HU11-01)
- Producción rollback: faltó harina → 422 y la leche NO se descontó. ✔ (SC-HU15-02)
- Cache insumos: `X-Cache: MISS` luego `HIT`; invalidación tras mutación. ✔ (HU-06)
- Suspensión: token STAFF válido (200) → tras suspend, 401 por blacklist. ✔ (SC-HU10-02)
- Rate limiting: 5 fallos (401/403) → 6º = 429 con `Retry-After: 900`. ✔ (SC-HU04-02)
- WebSocket: token válido recibe bienvenida; inválido rechazado; alerta low_stock
  retransmitida con `deficit` calculado. ✔ (SC-HU14-01/02)
- 48 tests unitarios en verde (dentro y fuera del contenedor).

## Entidades mencionadas
- [[entidades/pastrystock-manager]] — proyecto completado en su capa backend
- [[entidades/backend-pastrystock]] — módulo backend y su mapa de servicios/endpoints

## Conceptos relacionados
- [[conceptos/fifo-lotes-vencimiento]] — algoritmo de consumo por vencimiento
- [[conceptos/produccion-bom-transaccion-atomica]] — recetas y rollback
- [[conceptos/valorizacion-inventario]] — valor de activos y pérdida por mermas
- [[conceptos/rate-limiting-redis]] — bloqueo de login por IP
- [[conceptos/blacklist-jwt-redis]] — invalidación de sesión en JWT stateless
- [[conceptos/websockets-redis-pubsub]] — alertas en tiempo real
- [[conceptos/olap-export-desnormalizado]] — exportación plana para ETL
- [[conceptos/cache-first-paginacion]] — listados paginados cache-first
- [[conceptos/rbac]] — control de acceso por rol (ampliado)

## Notas de síntesis
El descuento por reconciliación (HU-11) ajusta `supply_items.current_stock` a nivel de
insumo, mientras que la valorización (HU-16) suma el stock a nivel de lote. En insumos
gestionados por lotes puede quedar una diferencia transitoria entre ambos niveles tras
una conciliación; es un comportamiento aceptado para el MVP (la conciliación es una
corrección a nivel de insumo, no de lote).
