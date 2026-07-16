# Despliegue en Railway — PastryStock Manager

Guía para desplegar el sistema en [Railway](https://railway.com). El proyecto se despliega como
**4 servicios** dentro de un mismo proyecto de Railway:

| Servicio | Tipo | Origen |
|---|---|---|
| **Postgres** | Base de datos (plugin) | Railway → New → Database → PostgreSQL |
| **Redis** | Base de datos (plugin) | Railway → New → Database → Redis |
| **backend** | FastAPI (Dockerfile) | carpeta `backend/` |
| **frontend** | Next.js (Dockerfile) | carpeta `frontend/` |

El frontend habla con el backend **desde el servidor** (`INTERNAL_API_URL`) y el navegador solo
usa `NEXT_PUBLIC_API_URL` para imágenes y el WebSocket de alertas.

---

## 0. Requisitos

- Cuenta en Railway (plan Hobby es suficiente para el MVP).
- Railway CLI: `npm i -g @railway/cli` (o `scoop install railway`).
- Autenticación (la haces tú en tu terminal): `railway login`.

## 1. Crear el proyecto y las bases de datos

```bash
railway init                       # crea el proyecto (elige un nombre)
railway add --database postgres    # agrega PostgreSQL
railway add --database redis       # agrega Redis
```
(También se puede desde el dashboard: **New → Database**.)

## 2. Servicio backend

Crea un servicio apuntando a la carpeta `backend/` (Root Directory = `backend`). Railway detecta
`backend/Dockerfile` y `backend/railway.json` (que ya definen el build y el arranque en `$PORT`
con `alembic upgrade head` previo).

**Variables de entorno del backend** (Settings → Variables). Usa *reference variables* para no
copiar secretos:

```
DATABASE_URL=postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/${{Postgres.PGDATABASE}}
REDIS_URL=${{Redis.REDIS_URL}}
SECRET_KEY=<pega aquí `openssl rand -hex 32`>
ENVIRONMENT=production
SUPERADMIN_EMAIL=tu-correo@pasteleria.pe
SUPERADMIN_PASSWORD=<contraseña fuerte>
CORS_ORIGINS=["https://TU-FRONTEND.up.railway.app"]
```

> `CORS_ORIGINS` necesita el dominio del frontend (paso 4). Déjalo provisional y actualízalo
> cuando tengas el dominio real; el backend se redeploya solo al cambiar la variable.

Genera el dominio público del backend: **Settings → Networking → Generate Domain**. Anótalo
(p. ej. `https://pastrystock-backend.up.railway.app`).

## 3. Sembrado automático en el arranque

El `startCommand` del backend (ver `backend/railway.json`) corre en cada deploy:

```
alembic upgrade head → seed_admin.py → seed_demo.py → gunicorn
```

Es decir, tras aplicar migraciones **crea el superadmin y siembra los datos de demostración
automáticamente**. Ambos seeds son idempotentes (no duplican) y no bloqueantes (si fallan,
el arranque continúa). Requiere que `SUPERADMIN_EMAIL` y `SUPERADMIN_PASSWORD` estén
configurados en las variables del backend.

> ¿No quieres datos de demo en un entorno real? Quita `seed_demo.py` del `startCommand`.

Sembrado manual (si lo necesitas puntualmente):

```bash
railway run --service backend python scripts/seed_admin.py
railway run --service backend python scripts/seed_demo.py
```

## 4. Servicio frontend

Crea otro servicio con Root Directory = `frontend`. Railway usa `frontend/Dockerfile` y
`frontend/railway.json`.

**Variables del frontend** (con el dominio del backend del paso 2):

```
NEXT_PUBLIC_API_URL=https://TU-BACKEND.up.railway.app/api/v1
INTERNAL_API_URL=https://TU-BACKEND.up.railway.app/api/v1
```

> `NEXT_PUBLIC_API_URL` se incrusta **en el build** (el Dockerfile la recibe como `ARG`), así que
> un cambio de esta variable exige **redeploy** del frontend, no solo reinicio.

Genera el dominio del frontend (**Networking → Generate Domain**) y **vuelve al backend** a poner
ese dominio en `CORS_ORIGINS`.

## 5. Desplegar

- **Opción A — CLI (sin GitHub):** desde cada carpeta, `railway up --service backend` y
  `railway up --service frontend` (o `railway up` con el servicio enlazado). Sube el código y
  construye con el Dockerfile.
- **Opción B — GitHub (auto-deploy):** inicializa git, sube el repo a GitHub y conecta cada
  servicio al repo indicando su Root Directory. Cada push despliega.

## 6. Verificación post-despliegue

- [ ] `https://TU-BACKEND.up.railway.app/health` responde `{"status": "ok"}`.
- [ ] `https://TU-BACKEND.up.railway.app/docs` carga la UI de OpenAPI.
- [ ] Logs del backend muestran `alembic ... Running upgrade ... 007` sin errores.
- [ ] Login en el frontend con el admin sembrado devuelve sesión.
- [ ] Crear categoría como ADMIN → 201 (Redis operativo).
- [ ] Un consumo que cruza el mínimo dispara el toast (WebSocket vivo → `NEXT_PUBLIC_API_URL` ok).
- [ ] Export `GET /reports/export?format=csv` descarga el CSV.

## Notas y problemas comunes

- **`$PORT`**: Railway asigna el puerto; el backend arranca con `--bind 0.0.0.0:$PORT` (ver
  `backend/railway.json`) y el frontend con `HOSTNAME=0.0.0.0` (ver `frontend/Dockerfile`).
- **Migraciones**: corren en el `startCommand` del backend en cada deploy (Alembic es idempotente).
- **Chicken-and-egg de dominios**: despliega backend → obtén su dominio → despliega frontend →
  pon el dominio del frontend en `CORS_ORIGINS` del backend.
- **Redis/Postgres privados**: se usan por la red interna de Railway (`RAILWAY_PRIVATE_DOMAIN`),
  sin exponerlos a Internet.
