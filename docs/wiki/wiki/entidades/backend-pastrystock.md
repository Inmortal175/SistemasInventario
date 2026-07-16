---
title: "Backend PastryStock"
type: modulo
tags: [backend, fastapi, sqlalchemy, redis, arquitectura-limpia]
---

# Backend PastryStock

## Descripción
Capa backend de [[entidades/pastrystock-manager]]: API FastAPI con SQLAlchemy 2.0 async,
Redis 7 y PostgreSQL 16, organizada en arquitectura limpia por capas
(domain → infrastructure → application → api → core). Cubre las 16 historias de usuario.

## Mapa de servicios (application/services)
- `AuthService` — login, rate limiting, seed superadmin.
- `CategoryService` — categorías cache-first.
- `LocationService` — ubicaciones con `LocationCode` validado.
- `SupplyService` — insumos, movimientos, conciliación, listado paginado.
- `BatchService` — lotes FIFO, valorización, alerta de vencimiento.
- `ProductionService` — recetas y producción BOM atómica.
- `DashboardService` — KPIs consolidados.
- `ReportService` — exportación CSV OLAP.
- `UserService` — CRUD usuarios, suspensión+blacklist, reset de contraseña con época de
  sesión ([[conceptos/recuperacion-contrasenas]]), audit-log.
- `AlertService` — publica alertas en Redis Pub/Sub.
- `SettingsService` — identidad visual y reglas de negocio de la instalación
  ([[conceptos/configuracion-sistema-en-bd]]).

## Endpoints por HU (28 rutas)
- HU-01 categorías · HU-02 movimientos · HU-03 ubicaciones · HU-04 auth (+rate limit)
- HU-05/06 supplies (CRUD + paginado) · HU-07 movements · HU-08 dashboard/kpis
- HU-09/13/16 batches · HU-10 users (suspend/reactivate/audit-log) · HU-11 reconciliation
- HU-12 reports/export · HU-14 ws/notifications · HU-15 recipes + production/produce
- HU-16 dashboard/financials

## Módulo de ajustes (2026-07-09)
- `system_settings`, fila única. `GET /api/v1/settings` es **público** (el login lo necesita
  antes de que exista sesión); `PATCH`, `POST/DELETE /logo` y
  `POST/DELETE /login-background/{device}` exigen SUPERADMIN.
- `app/core/uploads.py` — helper compartido de subida de imágenes con Pillow
  ([[conceptos/recorte-imagenes-1a1-y-aspecto]]). Usado por avatar, logo y fondos.
- `app/domain/category_icons.py` — lista blanca de iconos de categoría.
- `apply_app_name()` en `main.py` mantiene `/docs` y `/openapi.json` en sintonía con la
  interfaz.

## Aparece en
- [[fuentes/sesion-backend-completo-16-hu]] — sesión que completó el backend
- [[fuentes/sesion-frontend-nextjs-y-seed-admin]] — consumido por el frontend
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — settings, uploads, paginación de auditoría

## Relaciones
- [[entidades/pastrystock-manager]] — proyecto contenedor
- [[entidades/frontend-nextjs]] — cliente de esta API
- [[entidades/script-seed-admin]] — bootstrap del primer usuario
- [[entidades/script-seed-demo]] — escenario de simulación

## Notas
Migraciones Alembic: 001 (esquema inicial), 002 (lotes, recetas, `unit_cost`,
`locations.created_by`), 003 (`users.avatar_url`), **004** (`system_settings`),
**005** (fondos de login), **006** (reglas de negocio e identidad fiscal).
ENUMs creados en `sql/init.sql` con `create_type=False`; `ThemeName` y
`LoginBackgroundDevice` se guardan como texto, no como ENUM de PG, para que agregar una
paleta no exija migrar un tipo.

Perfil self-service en `/auth/me` (PATCH nombre y contraseña) — ver
[[conceptos/gestion-perfil-usuario]]. Scripts: `seed_admin.py`, `seed_demo.py`,
`check_expirations.py` (cron de vencimiento; el umbral ahora sale de Ajustes, no del
entorno), `reset_password.py` (recuperación CLI). El JWT incluye `iat` para la época de
sesión.

Dependencia añadida: **Pillow 11.1.0** (requiere reconstruir la imagen del backend).

**Tests:** 119 en total (unit + integración), cobertura **88.6%** (integración sola: 87.7%).
La suite de integración usa PostgreSQL/Redis reales sobre la base desechable `pastry_test`
([[conceptos/aislamiento-bd-tests]]); ya **no** toca la BD de desarrollo. Tras añadir una
migración hay que correr `scripts/setup_test_db.py` para que la BD de tests la reciba.

Las cifras de cobertura anteriores estaban subestimadas: `coverage.py` no trazaba el código
que corre tras el primer `await` a la base. Corregido con `concurrency = ["thread", "greenlet"]`
— ver [[conceptos/cobertura-y-greenlet-sqlalchemy]]. Sin cobertura de integración quedan
`endpoints/websocket.py` y `cache/pubsub_listener.py`.
