# Fase 3 — Plan Técnico (Diseño)

> **Artefacto SDD:** fase de **Diseño**. Traduce el *qué* del spec en el *cómo* técnico: stack,
> capas, contratos y decisiones de arquitectura. Se apoya en los diagramas de
> [`../architecture.md`](../architecture.md) y en el modelo de datos de
> [`../database-schema.md`](../database-schema.md), que forman parte de esta fase.

---

## 1. Stack (impuesto por el curso)

| Capa | Tecnología |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 async + asyncpg |
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind CSS |
| Base de datos | PostgreSQL 16 |
| Caché / mensajería | Redis 7 (cache + Pub/Sub + blacklist + rate limit) |
| Orquestación | Docker Compose (4 servicios) |
| Migraciones | Alembic |
| Pruebas | pytest + pytest-asyncio + httpx |

## 2. Arquitectura de capas (backend)

```
domain/          Entidades, enums, excepciones, value objects. SIN dependencias externas.
infrastructure/  Modelos ORM, repositorios concretos, cliente Redis, Pub/Sub.
application/      Servicios de caso de uso + schemas Pydantic v2.
api/             Routers FastAPI (v1), middlewares RBAC y manejadores de error.
core/            Config (pydantic-settings), security (JWT/Bcrypt), dependencias, uploads.
```

Regla de dependencia: `api → application → domain ← infrastructure`. La dirección se verifica
con el hecho de que `domain/` no importa FastAPI, SQLAlchemy ni Redis (Constitución, Art. III).

### Mapa de módulos reales

- **Endpoints** (`app/api/v1/endpoints/`): `auth`, `categories`, `locations`, `supplies`,
  `movements`, `batches`, `production`, `reports`, `dashboard`, `users`, `settings`, `websocket`.
- **Servicios** (`app/application/services/`): `auth`, `category`, `location`, `supply`,
  `batch`, `production`, `report`, `dashboard`, `user`, `settings`, `alert`.
- **Dominio** (`app/domain/`): `enums`, `exceptions`, `value_objects`, `category_icons`.
- **Infraestructura**: `database/` (modelos ORM, conexión), `cache/` (`redis_client`,
  `cache_keys`, `pubsub_listener`).

## 3. Decisiones de diseño (con su justificación)

| # | Decisión | Porqué |
|---|---|---|
| D-01 | Arquitectura limpia + `Protocol` para repos | Testabilidad (mocks), DIP, dominio aislado |
| D-02 | Cache-first en catálogo/listados | Latencia sub-ms en lecturas frecuentes (RNF-04) |
| D-03 | Modo degradado si Redis cae | Disponibilidad: la operación no depende del caché (RNF-05) |
| D-04 | `movement_history` inmutable | Auditoría confiable; correcciones vía `ADJUSTMENT` |
| D-05 | Lock pesimista + transacción atómica en stock | Evita condiciones de carrera (R-02) |
| D-06 | FIFO por `expiration_date` en consumo | Minimiza mermas por vencimiento (R-04) |
| D-07 | Producción BOM en una sola transacción con rollback | Atomicidad: o se descuentan todos los insumos o ninguno |
| D-08 | JWT + blacklist en Redis con TTL = exp restante | Suspensión de usuario invalida la sesión al instante |
| D-09 | Export desnormalizado (JOINs → tabla plana) | Deja datos OLAP-ready sin acoplar el OLTP |
| D-10 | Alertas por Redis Pub/Sub → WebSocket | Tiempo real sin polling REST (RNF-10) |
| D-11 | ENUMs definidos en `sql/init.sql`, ORM con `create_type=False` | Evita duplicación de tipos en primer boot |

## 4. Contrato de API (v1)

Prefijo: `/api/v1`. Convenciones REST + códigos de estado y `error_code` estables.

| Recurso | Rutas principales | HU |
|---|---|---|
| Auth | `POST /auth/login` | HU-04 |
| Categorías | `GET/POST /categories` | HU-01 |
| Ubicaciones | `GET/POST /locations` | HU-03 |
| Insumos | `GET/POST /supplies`, `GET /supplies/{id}` | HU-05, HU-06 |
| Movimientos | `POST /movements`, `GET /supplies/{id}/movements` | HU-02, HU-07, HU-09 |
| Conciliación | `POST /supplies/reconciliation` | HU-11 |
| Lotes | `POST /supplies/{id}/batches` | HU-13, HU-16 |
| Producción | `POST /production/produce`, `GET /production/history` | HU-15, HU-17 |
| Insumos/Productos | `GET /supplies?item_type=INGREDIENT\|FINISHED_PRODUCT` | HU-06, HU-17 |
| Reportes | `GET /reports/export` | HU-12 |
| Dashboard | `GET /dashboard/kpis`, `GET /dashboard/financials` | HU-08, HU-16 |
| Usuarios | `GET/POST /users`, `PATCH /users/{id}/suspend`, `GET /users/{id}/audit-log` | HU-10 |
| WebSocket | `WS /ws/notifications?token=` | HU-14 |

## 5. Modelo de datos (resumen)

Detalle completo en `database-schema.md`. Tablas núcleo:

- `users` — cuentas con rol (ENUM `user_role`), `is_active`.
- `locations` — código validado por `CHECK ~ '^(EST|REF|FRZ|CAB|CON|ALM)-\d{2}(-F\d{1,2})?$'`.
- `dynamic_categories` — categorías con slug, color e ícono.
- `supplies` — insumo o producto terminado (`item_type`) con `current_stock`, `minimum_stock`, FK a categoría y ubicación.
- `supply_batches` — lotes con `expiration_date`, `unit_cost`, `vendor_name` (FIFO + valorización).
- `recipes` / `recipe_items` — BOM para producción; `recipes.produces_supply_item_id` + `shelf_life_days` (HU-17).
- `production_runs` — **inmutable**: corrida de producción (receta, producto, cantidad, costo, ejecutor) (HU-17).
- `movement_history` — **inmutable**; FK `ondelete=RESTRICT`; sin `updated_at`.
- `system_settings`, `login_backgrounds` — parametrización.

**Modelo estrella OLAP-ready** (para el export, HU-12): `DimUsers`, `DimSupplies`,
`DimLocations`, `FactMovements`.

## 6. Estrategia de caché (Redis)

| Uso | Clave / canal | Política |
|---|---|---|
| Catálogo categorías | `categories:active:all`, `category:{id}` | TTL 3600 s, invalidación en mutación |
| Listado insumos | `supplies:page:{...}` | Cache-first, bypass en mutación |
| Alertas stock/vencimiento | canal `alerts:low_stock`, `alerts:expiration_critical` | Pub/Sub → WebSocket |
| Blacklist JWT | `jwt:blacklist:{jti}` | TTL = exp restante |
| Rate limit login | `login:rate_limit:{ip}` | 5 fallos / 15 min → bloqueo 900 s |

## 7. Seguridad

- Bcrypt para contraseñas; JWT firmado (claims `sub`, `email`, `role`, `exp`).
- RBAC en 3 capas (router `require_roles` → servicio `ALLOWED_MOVEMENTS_BY_ROLE` → BD).
- Rate limiting y blacklist de tokens en Redis.

## 8. Plan de pruebas (enlace a Fase 4)

TDD por capas: dominio puro → servicios (repos mockeados) → integración (BD `pastry_test` + Redis).
Cobertura ≥ 80 %. Detalle en `test-matrix.md` y sección de tareas `04-tasks.md` (bloque T-PRUEBAS).

## 9. Plan de despliegue (enlace a Fase 5)

Docker Compose con 4 servicios (backend, frontend, PostgreSQL, Redis); migraciones Alembic en el
primer boot; seed idempotente de admin y datos demo. Detalle en `05-deployment.md`.

## 10. Criterios de aceptación de la fase

- [x] Stack, capas y contrato de API definidos y trazables a HU.
- [x] Decisiones de diseño justificadas (D-01…D-11).
- [x] Modelo de datos y estrategia de caché documentados.
- [x] Salida lista para descomponer en tareas (`04-tasks.md`).
