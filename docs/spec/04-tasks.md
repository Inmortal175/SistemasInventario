# Fase 4 — Tareas (Plan de trabajo paso a paso)

> **Artefacto SDD central.** Descompone el `spec` y el `plan` en tareas atómicas, ordenadas y
> trazables. Es la evidencia de que el desarrollo se ejecutó **paso a paso siguiendo el ciclo de
> vida**, y no como código generado sin gobierno. Cada tarea enlaza a la HU que la origina y a la
> fase del ciclo de vida a la que pertenece.

## Leyenda

- **Estado:** ✅ hecha · 🔄 en curso · ⬜ pendiente
- **ID de tarea:** `T-<BLOQUE>-<NN>`
- **Depende de:** tareas que deben completarse antes (orden de ejecución).
- Cada tarea es verificable: se considera *hecha* solo cuando su criterio de aceptación (el
  escenario de la HU o el caso de prueba) pasa.

---

## Bloque 0 — Fundaciones (setup del proyecto)

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-SETUP-01 | Definir estructura de carpetas por capas (domain/infra/app/api/core) | Diseño | — | — | ✅ |
| T-SETUP-02 | Configurar `docker-compose` con 4 servicios + `.env.example` | Diseño | — | T-SETUP-01 | ✅ |
| T-SETUP-03 | Configurar SQLAlchemy async + asyncpg + Alembic | Diseño | — | T-SETUP-02 | ✅ |
| T-SETUP-04 | Definir ENUMs de dominio en `sql/init.sql` (`create_type=False`) | Diseño | — | T-SETUP-03 | ✅ |
| T-SETUP-05 | Configurar cliente Redis + `cache_keys` | Diseño | — | T-SETUP-02 | ✅ |
| T-SETUP-06 | Configurar pytest (asyncio, cobertura ≥80 %) y BD de test aislada | Pruebas | — | T-SETUP-03 | ✅ |

## Bloque 1 — Análisis y Especificación

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-ANL-01 | Redactar análisis (problema, alcance, RF/RNF, riesgos) → `01-analisis.md` | Análisis | — | — | ✅ |
| T-ANL-02 | Escribir las 16 HU con 35 escenarios BDD → `user-stories.md` | Análisis | HU-01…16 | T-ANL-01 | ✅ |
| T-ANL-03 | Definir modelo estrella OLAP-ready (Dim/Fact) | Análisis | HU-12 | T-ANL-02 | ✅ |
| T-ANL-04 | Formalizar constitución del proyecto → `00-constitution.md` | Análisis | — | T-ANL-01 | ✅ |

## Bloque 2 — Diseño

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-DIS-01 | Diseñar arquitectura de capas + diagramas → `architecture.md` | Diseño | — | T-ANL-02 | ✅ |
| T-DIS-02 | Diseñar esquema relacional + constraints → `database-schema.md` | Diseño | HU-05,13 | T-DIS-01 | ✅ |
| T-DIS-03 | Diseñar estrategia de caché (claves, TTL, invalidación) | Diseño | HU-01,06 | T-DIS-01 | ✅ |
| T-DIS-04 | Definir contrato de API v1 y códigos de error | Diseño | HU-01…16 | T-DIS-01 | ✅ |
| T-DIS-05 | Diseñar decisiones D-01…D-11 con justificación → `03-plan.md` | Diseño | — | T-DIS-01 | ✅ |

## Bloque 3 — Núcleo de dominio (TDD primero)

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-DOM-01 | Prueba + implementación de `LocationCode` (regex, normalización, tipo) | Pruebas→Impl | HU-03 | T-SETUP-06 | ✅ |
| T-DOM-02 | Prueba + implementación de excepciones de dominio con contexto | Pruebas→Impl | HU-02 | T-SETUP-06 | ✅ |
| T-DOM-03 | Prueba + `ALLOWED_MOVEMENTS_BY_ROLE` (STAFF=EXIT/WASTE) | Pruebas→Impl | HU-02 | T-DOM-02 | ✅ |
| T-DOM-04 | Definir enums (`MovementType`, `UserRole`, `LocationType`) | Impl | — | T-DOM-01 | ✅ |

## Bloque 4 — Autenticación y usuarios

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-AUTH-01 | Hash Bcrypt + emisión/verificación JWT (`core/security`) | Impl | HU-04 | T-DOM-04 | ✅ |
| T-AUTH-02 | Endpoint `POST /auth/login` + schema | Impl | HU-04 | T-AUTH-01 | ✅ |
| T-AUTH-03 | Rate limiting de login en Redis (5/15min → 900 s) | Impl | HU-04 | T-AUTH-02 | ✅ |
| T-AUTH-04 | Middleware RBAC `require_roles` + manejadores de error | Impl | HU-01…16 | T-AUTH-01 | ✅ |
| T-USR-01 | CRUD de usuarios (SUPERADMIN) `user_service` + endpoints | Impl | HU-10 | T-AUTH-04 | ✅ |
| T-USR-02 | Suspensión lógica + blacklist JWT en Redis (TTL=exp) | Impl | HU-10 | T-USR-01 | ✅ |
| T-USR-03 | Endpoint de audit-log por usuario | Impl | HU-10 | T-USR-01 | ✅ |

## Bloque 5 — Catálogo (categorías, ubicaciones)

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-CAT-01 | `category_service` cache-first (Redis→PostgreSQL) + slug | Impl | HU-01 | T-DIS-03 | ✅ |
| T-CAT-02 | Endpoints categorías + validación 422 + conflicto 409 | Impl | HU-01 | T-CAT-01 | ✅ |
| T-CAT-03 | Modo degradado si Redis cae (fallback + warning) | Impl | HU-01 | T-CAT-01 | ✅ |
| T-LOC-01 | `location_service` con normalización de código | Impl | HU-03 | T-DOM-01 | ✅ |
| T-LOC-02 | Endpoints ubicaciones + rechazo de formato inválido | Impl | HU-03 | T-LOC-01 | ✅ |

## Bloque 6 — Insumos y movimientos (corazón del OLTP)

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-SUP-01 | CRUD de insumos con validación de FK (categoría/ubicación) | Impl | HU-05 | T-CAT-01, T-LOC-01 | ✅ |
| T-SUP-02 | Listado con filtros + paginación cacheada (offset) | Impl | HU-06 | T-SUP-01 | ✅ |
| T-SUP-03 | Consumo `EXIT` con lock pesimista + transacción atómica | Impl | HU-02 | T-DOM-02 | ✅ |
| T-SUP-04 | Validación de stock no negativo (dominio + constraint BD) | Impl | HU-02 | T-SUP-03 | ✅ |
| T-SUP-05 | Registro inmutable en `movement_history` (before/after) | Impl | HU-02,07 | T-SUP-03 | ✅ |
| T-SUP-06 | Reabastecimiento `ENTRY` (ADMIN) | Impl | HU-09 | T-SUP-03 | ✅ |
| T-SUP-07 | Historial de movimientos por insumo (auditoría paginada) | Impl | HU-07 | T-SUP-05 | ✅ |
| T-SUP-08 | Conciliación `ADJUSTMENT` (Δ físico vs registrado) | Impl | HU-11 | T-SUP-05 | ✅ |

## Bloque 7 — Lotes, FIFO y producción

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-BAT-01 | `supply_batches` + recálculo de stock total por sumatoria de lotes | Impl | HU-13 | T-SUP-01 | ✅ |
| T-BAT-02 | Consumo FIFO por `expiration_date` con desglose por lote | Impl | HU-13 | T-BAT-01, T-SUP-03 | ✅ |
| T-BAT-03 | Alerta predictiva de lotes próximos a vencer (background task) | Impl | HU-13 | T-BAT-01 | ✅ |
| T-BAT-04 | `unit_cost` + `vendor_name` en lote (proveedor/valorización) | Impl | HU-16 | T-BAT-01 | ✅ |
| T-PRD-01 | Recetas (BOM) `recipes`/`recipe_items` + `production_service` | Impl | HU-15 | T-BAT-02 | ✅ |
| T-PRD-02 | Producción atómica con rollback ante déficit de ingrediente | Impl | HU-15 | T-PRD-01 | ✅ |

## Bloque 8 — Analítica, dashboard y tiempo real

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-DSH-01 | KPIs consolidados (`GET /dashboard/kpis`) leídos de Redis | Impl | HU-08 | T-SUP-05 | ✅ |
| T-DSH-02 | Valorización financiera (`GET /dashboard/financials`) | Impl | HU-16 | T-BAT-04 | ✅ |
| T-RPT-01 | Export desnormalizado CSV/Excel OLAP-ready (JOINs → tabla plana) | Impl | HU-12 | T-SUP-05 | ✅ |
| T-RPT-02 | Restricción de reportes globales a ADMIN+ (403 a STAFF) | Impl | HU-12 | T-RPT-01 | ✅ |
| T-ALR-01 | `alert_service` publica en canales Redis Pub/Sub | Impl | HU-02,14 | T-SUP-03 | ✅ |
| T-WS-01 | Handshake WebSocket con auth JWT + grupos por rol | Impl | HU-14 | T-AUTH-01 | ✅ |
| T-WS-02 | `pubsub_listener` retransmite alertas a WebSocket en tiempo real | Impl | HU-14 | T-ALR-01, T-WS-01 | ✅ |

## Bloque 9 — Frontend (Next.js 15)

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-FE-01 | Layout dashboard + navegación responsiva + login | Impl | HU-04 | T-AUTH-02 | ✅ |
| T-FE-02 | Vistas de categorías, ubicaciones, insumos, movimientos | Impl | HU-01,03,05,06 | T-FE-01 | ✅ |
| T-FE-03 | Vistas de lotes, producción, conciliación, reportes | Impl | HU-11,12,13,15 | T-FE-02 | ✅ |
| T-FE-04 | Dashboard con KPIs + valorización + toasts por WebSocket | Impl | HU-08,14,16 | T-WS-02 | ✅ |
| T-FE-05 | Gestión de usuarios, perfil, ajustes/branding | Impl | HU-10 | T-USR-01 | ✅ |

## Bloque 10 — Pruebas (SDT)

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-TST-01 | Unitarias de dominio (`test_domain_value_objects`) | Pruebas | HU-01,02,03 | T-DOM-01 | ✅ |
| T-TST-02 | Unitarias de servicios (supply, category, location) | Pruebas | HU-01,02,03,05 | Bloque 6 | ✅ |
| T-TST-03 | Unitarias FIFO, producción, conciliación, reportes | Pruebas | HU-11,12,13,15 | Bloque 7-8 | ✅ |
| T-TST-04 | Unitaria de rate limit de auth | Pruebas | HU-04 | T-AUTH-03 | ✅ |
| T-TST-05 | Integración de API (`test_api`, `test_advanced_api`) | Pruebas | varios | Bloque 6-8 | ✅ |
| T-TST-06 | Verificar cobertura ≥ 80 % y matriz `test-matrix.md` | Pruebas | — | T-TST-01…05 | ✅ |

## Bloque 11 — Despliegue

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-DEP-01 | Migraciones Alembic (001→008) aplicables en primer boot | Despliegue | — | T-DIS-02 | ✅ |
| T-DEP-02 | Seed idempotente de admin + datos demo | Despliegue | — | T-DEP-01 | ✅ |
| T-DEP-03 | `docker-compose up` levanta los 4 servicios sanos | Despliegue | — | Bloque 6-9 | ✅ |
| T-DEP-04 | `docker-compose.prod.yml` + variables de entorno de producción | Despliegue | — | T-DEP-03 | ✅ |
| T-DEP-05 | Checklist de despliegue y verificación → `05-deployment.md` | Despliegue | — | T-DEP-03 | ✅ |

## Bloque 12 — Documentación y trazabilidad

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-DOC-01 | Registrar sesiones y conceptos en la wiki (`docs/wiki/`) | Transversal | — | — | ✅ |
| T-DOC-02 | Cerrar matriz de trazabilidad HU→Tarea→Código→Test → `06-traceability.md` | Transversal | HU-01…16 | Todos | ✅ |
| T-DOC-03 | Elaborar informe de trabajo final con anexos y evidencias | Transversal | — | T-DOC-02 | 🔄 |

## Bloque 13 — Producto terminado y registro de producción (HU-17)

> Cambio solicitado por el usuario final (dueño): la pastelería produce y guarda tortas en
> refrigeración para sostener días de alta demanda. El producto terminado debe ser inventario y
> cada corrida de producción debe quedar registrada.

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-FIN-01 | Análisis del vacío: `produce` descontaba insumos pero no registraba lo producido | Análisis | HU-17 | — | ✅ |
| T-FIN-02 | Especificar HU-17 (4 escenarios) en `user-stories.md` | Análisis | HU-17 | T-FIN-01 | ✅ |
| T-FIN-03 | `ItemType` (INGREDIENT/FINISHED_PRODUCT) en dominio | Diseño→Impl | HU-17 | T-FIN-02 | ✅ |
| T-FIN-04 | Migración 007: `item_type`, `recipes.produces_supply_item_id` + `shelf_life_days`, tabla `production_runs` | Diseño→Impl | HU-17 | T-FIN-03 | ✅ |
| T-FIN-05 | `produce`: ENTRY del producto terminado (lote + vencimiento) en la misma transacción | Impl | HU-17 | T-FIN-04 | ✅ |
| T-FIN-06 | `produce`: asentar la corrida en `production_runs` | Impl | HU-17 | T-FIN-05 | ✅ |
| T-FIN-07 | Endpoint `GET /production/history` + repo + schemas | Impl | HU-17 | T-FIN-06 | ✅ |
| T-FIN-08 | Frontend: producto terminado en alta de insumo, receta→producto+vida útil, historial | Impl | HU-17 | T-FIN-07 | ✅ |
| T-FIN-09 | Verificación: migración 007 aplicada + suite pytest verde (120 tests, 88% cob.) | Pruebas | HU-17 | T-FIN-08 | ✅ |

## Bloque 14 — Refinamientos de UX y datos (feedback del usuario)

> Tras usar HU-17, el usuario final observó: (a) registrar el producto como "insumo" es tedioso y
> confuso; (b) la auditoría de movimientos se lee como código, no en español; (c) el export OLAP
> podía enriquecerse. Ajustes gobernados por SDD.

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-REF-01 | Auditoría legible: resumen en español con insumo, unidad y motivo | Impl | HU-10 | — | ✅ |
| T-REF-02 | Auto-crear el producto terminado desde la receta (sin registrarlo como insumo) | Impl | HU-17 | — | ✅ |
| T-REF-03 | Sección propia "Productos terminados" (filtro `item_type` en API + UI + nav) | Impl | HU-17 | T-REF-02 | ✅ |
| T-REF-04 | OLAP: añadir `item_type`, `unit_cost`, `total_cost`, `notes` al export | Impl | HU-12 | — | ✅ |
| T-REF-05 | Verificación: suite pytest verde + typecheck frontend | Pruebas | — | T-REF-01…04 | ✅ |

## Bloque 15 — Despliegue en producción (Railway vía GitHub)

> El Bloque 11 cubre el despliegue **local/demo** con Docker Compose. Este bloque lleva el sistema
> a un entorno **público y permanente** en Railway, como 4 servicios (Postgres, Redis, backend,
> frontend). Decisión de método: **auto-deploy desde GitHub** (cada push a `main` despliega), sin
> Railway CLI — el repositorio queda además como evidencia del ciclo de vida. Guía operativa
> detallada en `docs/deployment-railway.md`.

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-RW-01 | `backend/Dockerfile` de producción (gunicorn + workers uvicorn, bind a `$PORT`) | Despliegue | — | T-DEP-04 | ✅ |
| T-RW-02 | `frontend/Dockerfile` (build standalone, `HOSTNAME=0.0.0.0`, `ARG NEXT_PUBLIC_API_URL`) | Despliegue | — | T-DEP-04 | ✅ |
| T-RW-03 | `backend/railway.json`: builder DOCKERFILE, `startCommand` → `sh start.sh`, healthcheck `/health` | Despliegue | — | T-RW-01 | ✅ |
| T-RW-04 | `frontend/railway.json`: builder DOCKERFILE + política de reinicio | Despliegue | — | T-RW-02 | ✅ |
| T-RW-05 | Redactar guía de despliegue → `deployment-railway.md` | Despliegue | — | T-RW-03, T-RW-04 | ✅ |
| T-RW-06 | Verificar que `.gitignore` excluye `.env` y secretos antes de publicar (solo `.env.example` rastreado) | Despliegue | — | — | ✅ |
| T-RW-07 | Publicar el repositorio en GitHub (rama `main`) | Despliegue | — | T-RW-06 | ✅ |
| T-RW-08 | Crear proyecto en Railway + plugins PostgreSQL y Redis | Despliegue | — | T-RW-07 | ✅ |
| T-RW-09 | Servicio `backend` conectado al repo (Root Directory = `backend`, auto-deploy en push) | Despliegue | — | T-RW-08 | ✅ |
| T-RW-10 | Variables del backend: `DATABASE_URL` (con `+asyncpg`), `SECRET_KEY`, `ENVIRONMENT`, `SUPERADMIN_*` | Despliegue | HU-04 | T-RW-09 | ✅ |
| T-RW-11 | Generar dominio público del backend (Networking → Generate Domain) | Despliegue | — | T-RW-10 | ✅ |
| T-RW-12 | Servicio `frontend` (Root Directory = `frontend`) + `NEXT_PUBLIC_API_URL`/`INTERNAL_API_URL` + dominio | Despliegue | — | T-RW-11 | ✅ |
| T-RW-13 | Cerrar `CORS_ORIGINS` del backend con el dominio real del frontend (redeploy) | Despliegue | — | T-RW-12 | ✅ |
| T-RW-14 | Decidir si `seed_demo.py` permanece en el `startCommand` del entorno productivo | Despliegue | — | T-RW-10 | ✅ |
| T-RW-15 | Verificar en logs: migraciones `000→008` aplicadas y arranque de gunicorn | Pruebas | — | T-RW-13 | ✅ |
| T-RW-16 | Ejecutar checklist post-despliegue: `/health`, `/docs`, login, categoría 201 (Redis), toast por WebSocket, export CSV | Pruebas | HU-01,04,12,14 | T-RW-23 | ⬜ |
| T-RW-17 | Registrar la sesión de despliegue en la wiki (`docs/wiki/`) | Transversal | — | T-RW-16 | ✅ |
| T-RW-18 | Migración `000`: crear los ENUMs desde Alembic (`init.sql` no corre en PostgreSQL gestionado) | Despliegue | — | T-RW-08 | ✅ |
| T-RW-19 | `static/` creado con permisos de `appuser` en el Dockerfile (está en `.gitignore`, no viaja al build) | Despliegue | HU-16 | T-RW-01 | ✅ |
| T-RW-20 | `CORS_ORIGINS` leído como texto: `list[str]` rompía el arranque por el json.loads de pydantic-settings | Despliegue | — | T-RW-13 | ✅ |
| T-RW-21 | `start.sh`: migraciones con `timeout` y arranque desacoplado (Alembic no puede secuestrar el healthcheck) | Despliegue | — | T-RW-03 | ✅ |
| T-RW-22 | Subir `next` a 15.1.11: Railway bloquea el build por CVE-2025-66478 (CRITICAL) y 3 más | Despliegue | — | T-RW-12 | ✅ |
| T-RW-23 | `REDIS_URL` válida en el backend (bloquea el login: `AuthService` depende de Redis) | Despliegue | HU-04 | T-RW-08 | ⬜ |
| T-RW-24 | Montar Volume en `/app/static`: el FS de Railway es efímero, los avatares no sobreviven al redeploy | Despliegue | HU-16 | T-RW-19 | ⬜ |
| T-RW-25 | Resolver la carrera del seed de superadmin entre los workers de gunicorn (`UniqueViolationError` en cada arranque) | Implementación | HU-04 | T-RW-15 | ⬜ |
| T-RW-26 | Investigar el cuelgue de Alembic en Railway (se resolvió reiniciando PostgreSQL; causa raíz sin confirmar) | Pruebas | — | T-RW-21 | ⬜ |

---

## Bloque 16 — UX de contraseñas y auditoría CSRF

> Sesión posterior al despliegue. La visibilidad de contraseña es una petición directa de usuario;
> la auditoría CSRF documenta una postura de seguridad que ya existía pero no estaba escrita.

| ID | Tarea | Fase | HU | Depende | Estado |
|---|---|---|---|---|---|
| T-UX-01 | Componente `PasswordInput` con botón de revelar/ocultar (accesible: `aria-label` + `aria-pressed`) | Implementación | HU-04 | — | ✅ |
| T-UX-02 | Aplicar `PasswordInput` en los 6 campos: login, alta de usuario, reset de contraseña, cambio de contraseña (×3) | Implementación | HU-04, HU-10 | T-UX-01 | ✅ |
| T-SEC-01 | Auditar la protección CSRF de la autenticación | Pruebas | HU-04 | — | ✅ |
| T-SEC-02 | Validación explícita de `Origin` en los 3 route handlers POST (defensa en profundidad, opcional) | Implementación | HU-04 | T-SEC-01 | ⬜ |

---

## Resumen de ejecución

| Bloque | Tareas | Hechas | Fase dominante |
|---|---|---|---|
| 0 Fundaciones | 6 | 6 | Diseño |
| 1 Análisis/Spec | 4 | 4 | Análisis |
| 2 Diseño | 5 | 5 | Diseño |
| 3 Dominio | 4 | 4 | Pruebas→Impl |
| 4 Auth/Usuarios | 7 | 7 | Implementación |
| 5 Catálogo | 5 | 5 | Implementación |
| 6 Insumos/Movimientos | 8 | 8 | Implementación |
| 7 Lotes/Producción | 6 | 6 | Implementación |
| 8 Analítica/Tiempo real | 7 | 7 | Implementación |
| 9 Frontend | 5 | 5 | Implementación |
| 10 Pruebas | 6 | 6 | Pruebas |
| 11 Despliegue | 5 | 5 | Despliegue |
| 12 Documentación | 3 | 2 | Transversal |
| 13 Producto terminado (HU-17) | 9 | 9 | Impl→Pruebas |
| 14 Refinamientos UX/datos | 5 | 5 | Implementación |
| 15 Despliegue en Railway | 26 | 22 | Despliegue |
| 16 UX contraseñas / CSRF | 4 | 3 | Impl→Pruebas |
| **Total** | **115** | **109** | — |

> **Pendientes:** el sistema está desplegado y sirviendo en Railway (backend y frontend con dominio
> público, migraciones `000→008` aplicadas). El login todavía devuelve 500 por **T-RW-23**:
> `REDIS_URL` no tiene un valor válido y `AuthService` recibe Redis como dependencia obligatoria.
> Cerrada esa tarea se puede ejecutar el checklist **T-RW-16**. Quedan además el Volume para los
> estáticos (T-RW-24), la carrera del seed entre workers (T-RW-25) y la causa raíz del cuelgue de
> Alembic (T-RW-26). T-DOC-03 (informe final) queda al final, ya que consume el resto de artefactos
> como anexos e incluirá la URL pública del sistema desplegado.
