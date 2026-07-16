# Fase 5 — Despliegue

> **Artefacto SDD:** fase de **Despliegue** del ciclo de vida. Documenta cómo se lleva el sistema
> desde el código a un entorno ejecutable y verificable, con su checklist de evidencia. Se apoya
> en `docker-compose.yml`, `docker-compose.prod.yml` y `README.md`.

---

## 1. Topología

Docker Compose orquesta **4 servicios**:

| Servicio | Imagen base | Puerto | Rol |
|---|---|---|---|
| `frontend` | Next.js 15 (Node) | 3000 | UI (App Router) |
| `backend` | FastAPI (Python) | 8000 | API REST + WebSocket |
| `db` | PostgreSQL 16 | 5432 | Persistencia OLTP |
| `redis` | Redis 7 | 6379 | Caché, Pub/Sub, blacklist, rate limit |

## 2. Variables de entorno

Configuradas vía `.env` (plantilla en `.env.example`). Las principales:

| Variable | Uso |
|---|---|
| `DATABASE_URL` | Cadena de conexión asyncpg a PostgreSQL |
| `REDIS_URL` | Conexión a Redis |
| `SECRET_KEY` | Firma de JWT |

> Nunca versionar `.env` con secretos reales. `SECRET_KEY` debe ser fuerte y único por entorno.

## 3. Procedimiento de despliegue (local / demo)

```bash
# 1. Variables de entorno
cp .env.example .env            # y ajustar SECRET_KEY

# 2. Levantar los 4 servicios
docker-compose up -d

# 3. Verificar contenedores sanos
docker-compose ps

# 4. Aplicar migraciones (primer arranque)
docker-compose exec backend alembic upgrade head

# 5. (Opcional) Seed de admin y datos demo
docker-compose exec backend python scripts/seed_admin.py   # admin idempotente
docker-compose exec backend python scripts/seed_demo.py    # datos de demostración
```

Servicios disponibles tras el arranque:

- Frontend: <http://localhost:3000>
- API: <http://localhost:8000>
- Docs interactivas (OpenAPI): <http://localhost:8000/docs>

## 4. Migraciones aplicadas (Alembic)

| Revisión | Contenido |
|---|---|
| 001 | Esquema inicial (users, locations, categories, supplies, movement_history) |
| 002 | Lotes, recetas y costos (`supply_batches`, `recipes`) |
| 003 | `avatar_url` en usuarios |
| 004 | `system_settings` |
| 005 | `login_backgrounds` |
| 006 | Reglas de negocio de configuración |
| 007 | Producto terminado y registro de producción (`item_type`, `production_runs`, `recipes.produces_supply_item_id`/`shelf_life_days`) |
| 008 | Lista de preparación persistida (`production_run_items`: snapshot por ingrediente con unidad, ubicación y desglose FIFO de lotes) |

Los ENUMs se crean en `sql/init.sql` en el primer boot de PostgreSQL; el ORM los referencia con
`create_type=False` para evitar duplicados (ver Constitución, Art. IV).

## 5. Despliegue productivo

`docker-compose.prod.yml` define la variante de producción (imágenes optimizadas, sin hot-reload,
variables de entorno endurecidas). Diferencias frente al entorno local:

- `SECRET_KEY` y credenciales inyectadas por el entorno, no por `.env` versionado.
- Sin montaje de volúmenes de código fuente (build inmutable).
- `restart: unless-stopped` en los servicios.

## 6. Checklist de verificación post-despliegue

- [ ] `docker-compose ps` muestra los 4 servicios en estado `Up`/`healthy`.
- [ ] `GET /health` responde 200 (o `/docs` carga la UI de OpenAPI).
- [ ] Login con el admin sembrado devuelve JWT válido (HU-04).
- [ ] Crear categoría como ADMIN devuelve 201 y queda en Redis (HU-01).
- [ ] STAFF que intenta crear categoría recibe 403 (HU-01 SC-03) — RBAC operativo.
- [ ] Consumo que cruza el mínimo dispara toast en el dashboard (HU-02 + HU-14) — WebSocket vivo.
- [ ] Export `GET /reports/export?format=csv` descarga el CSV desnormalizado (HU-12).
- [ ] `alembic current` coincide con la última revisión (008).

## 7. Operación y respaldo (notas)

- **Logs:** `docker-compose logs -f backend`.
- **Respaldo BD:** `pg_dump` sobre el servicio `db` (fuera del alcance del MVP automatizarlo).
- **Rollback de migración:** `alembic downgrade -1` (con precaución; el historial es inmutable a
  nivel de datos, no de esquema).

## 8. Criterios de aceptación de la fase

- [x] Topología y variables de entorno documentadas.
- [x] Procedimiento reproducible de arranque + migraciones + seed.
- [x] Variante de producción definida.
- [x] Checklist de verificación funcional trazable a HU.
