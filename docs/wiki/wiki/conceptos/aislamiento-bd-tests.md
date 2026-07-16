---
title: "Aislamiento de la BD de tests de integración"
tags: [testing, integracion, base-datos, ci, buenas-practicas]
source_count: 1
---

# Aislamiento de la BD de tests de integración

## Definición
Las pruebas de integración corren contra una base **desechable** `pastry_test` (y Redis
en el índice `/1`), nunca contra la BD de desarrollo `pastry_inventory`.

## Problema que resuelve
El conftest de integración hace `TRUNCATE ... CASCADE` antes de cada test. Al compartir
`DATABASE_URL` con desarrollo, cada corrida de `pytest` borraba todos los datos vivos y el
superadmin sembrado, dejando fixtures `*-<hex>@test.local`. Esto bloqueó el login del
usuario varias veces.

## Implementación
- `tests/integration/conftest.py` deriva `pastry_test` de `DATABASE_URL`
  (`rpartition('/')`), con override por `TEST_DATABASE_URL`; y Redis `/1`, override
  `TEST_REDIS_URL`.
- `scripts/setup_test_db.py` (idempotente): crea `pastry_test`, aplica `sql/init.sql`
  (ENUMs) y `alembic upgrade head` con `DATABASE_URL` apuntando a la base de tests.
- El `client` de tests ya sobreescribe `get_async_session`/`get_redis` con la sesión y
  Redis de test, así que ninguna ruta toca la BD de desarrollo.

## Fuentes que lo mencionan
- [[fuentes/sesion-avatar-pyjwt-y-test-db]] — corrección definitiva del truncado

## Perspectivas/decisiones
Se optó por una base separada en la misma instancia Postgres (no un contenedor nuevo):
mínimo cambio, cero infra extra. Verificado: tras `pytest`, el superadmin de desarrollo
SOBREVIVE y no aparecen fixtures en `pastry_inventory`.

## Contradicciones detectadas
Ninguna.
