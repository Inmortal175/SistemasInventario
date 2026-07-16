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

> **Método de despliegue: GitHub con auto-deploy.** Railway se conecta al repositorio y cada push
> a `main` despliega. No hace falta la CLI de Railway; todo se hace desde el navegador. Los pocos
> pasos que sí requieren CLI están marcados como *opcionales* al final.

---

## 0. Requisitos

- Cuenta en Railway (plan Hobby es suficiente para el MVP).
- Cuenta de GitHub y el repositorio publicado (ver paso 1).

## 1. Publicar el repositorio en GitHub

Railway despliega desde el repo, así que este es el primer paso.

> ⚠️ **Antes del primer push:** confirma que `.gitignore` excluye `.env` y cualquier archivo con
> secretos. Si un secreto entra al historial de git, quitarlo después implica reescribir historia.
> `SECRET_KEY` y las contraseñas se configuran como variables en Railway, nunca en el repo.

```bash
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
```

## 2. Crear el proyecto y las bases de datos

En el dashboard de Railway:

1. **New Project** → elige un nombre (p. ej. `pastrystock`).
2. Dentro del proyecto: **New → Database → PostgreSQL**.
3. Otra vez: **New → Database → Redis**.

Ambos quedan accesibles por la red privada del proyecto, sin exponerse a Internet.

## 3. Servicio backend

**New → GitHub Repo** → selecciona tu repositorio. Luego, en **Settings → Source**, pon
**Root Directory = `backend`**. Railway detecta `backend/Dockerfile` y `backend/railway.json` (que
ya definen el build y el arranque en `$PORT` con `alembic upgrade head` previo) y activa el
auto-deploy en cada push a `main`.

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

> `CORS_ORIGINS` necesita el dominio del frontend (paso 5). Déjalo provisional y actualízalo
> cuando tengas el dominio real; el backend se redeploya solo al cambiar la variable.

Genera el dominio público del backend: **Settings → Networking → Generate Domain**. Anótalo
(p. ej. `https://pastrystock-backend.up.railway.app`).

## 4. Sembrado automático en el arranque

El `startCommand` del backend (ver `backend/railway.json`) corre en cada deploy:

```
alembic upgrade head → seed_admin.py → seed_demo.py → gunicorn
```

Es decir, tras aplicar migraciones **crea el superadmin y siembra los datos de demostración
automáticamente**. Ambos seeds son idempotentes (no duplican) y no bloqueantes (si fallan,
el arranque continúa). Requiere que `SUPERADMIN_EMAIL` y `SUPERADMIN_PASSWORD` estén
configurados en las variables del backend.

> ¿No quieres datos de demo en un entorno real? Quita `seed_demo.py` del `startCommand`.

## 5. Servicio frontend

Repite el paso 3 con el **mismo repositorio**: **New → GitHub Repo** y, en Settings → Source,
**Root Directory = `frontend`**. Railway usa `frontend/Dockerfile` y `frontend/railway.json`.

> Dos servicios apuntando al mismo repo con distinto Root Directory es lo normal en un monorepo.
> Cada push dispara el build de ambos.

**Variables del frontend** (con el dominio del backend del paso 3):

```
NEXT_PUBLIC_API_URL=https://TU-BACKEND.up.railway.app/api/v1
INTERNAL_API_URL=https://TU-BACKEND.up.railway.app/api/v1
```

> `NEXT_PUBLIC_API_URL` se incrusta **en el build** (el Dockerfile la recibe como `ARG`), así que
> un cambio de esta variable exige **redeploy** del frontend, no solo reinicio.

Genera el dominio del frontend (**Networking → Generate Domain**) y **vuelve al backend** a poner
ese dominio en `CORS_ORIGINS`.

## 6. Desplegar

Con los servicios conectados al repo, **cada push a `main` despliega automáticamente**:

```bash
git push
```

También puedes forzar un despliegue desde el dashboard (**Deployments → Redeploy**), útil cuando
solo cambiaste una variable de entorno y no hay commit nuevo que empujar.

## 7. Verificación post-despliegue

- [ ] `https://TU-BACKEND.up.railway.app/health` responde `{"status": "ok"}`.
- [ ] `https://TU-BACKEND.up.railway.app/docs` carga la UI de OpenAPI.
- [ ] Logs del backend muestran `alembic ... Running upgrade ... 008` sin errores.
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

---

## Apéndice — CLI de Railway (opcional)

No es necesaria para desplegar por GitHub, pero sirve para tareas puntuales desde la terminal:

```bash
npm i -g @railway/cli        # o: scoop install railway
railway login               # abre el navegador
railway link                # enlaza esta carpeta al proyecto
```

Una vez enlazado:

```bash
railway logs --service backend                              # ver logs en vivo
railway run --service backend python scripts/seed_admin.py  # sembrado manual
railway run --service backend alembic current               # revisión aplicada
```
