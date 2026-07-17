---
title: "Sesión: despliegue en Railway, auditoría CSRF y visibilidad de contraseñas"
date: 2026-07-17
source_url: ""
source_path: ""
type: sesion-desarrollo
tags: [despliegue, railway, alembic, docker, seguridad, csrf, ux, cve]
---

# Sesión: despliegue en Railway, auditoría CSRF y visibilidad de contraseñas

## Resumen
Puesta en producción del sistema en Railway (backend + frontend con dominio público) tras
una cadena de siete fallos encadenados, cada uno enmascarando al siguiente. Se añadió
además el toggle de visibilidad en los campos de contraseña y se auditó la protección
CSRF, que resultó ser correcta pero implícita y sin documentar.

## Ideas clave

- **Un PaaS no es docker-compose.** Casi todos los fallos vinieron de asumir que lo que
  compose hace por ti (construir `DATABASE_URL` desde piezas, ejecutar `init.sql`, montar
  `static/`) alguien lo haría también en Railway. No lo hace nadie.
- **Reproducir en local vale más que diez teorías.** Las primeras horas se fueron en
  hipótesis probadas contra ciclos de build de 5 minutos. Al construir la imagen de
  producción en local desde un contexto de solo-git, cada duda se resolvió en segundos.
  Ver [[conceptos/reproducir-el-contenedor-de-produccion-en-local]].
- **Las migraciones no deben poder bloquear el arranque.** Alembic colgado con `&&`
  secuestraba la ventana entera del healthcheck y el contenedor moría sin un solo error en
  los logs. Ver [[conceptos/arranque-de-contenedor-y-healthcheck]].
- **El backend no tiene superficie CSRF** porque autentica con Bearer, no con cookies.
  Ver [[conceptos/proteccion-csrf-bearer-vs-cookies]].

## Fallos encontrados y su causa

| Síntoma | Causa real |
|---|---|
| `Railpack could not determine how to build` | Railway construía desde la raíz; faltaba **Root Directory** = `backend`/`frontend` |
| `type "user_role" does not exist` | `sql/init.sql` solo lo ejecuta compose; el PaaS nunca lo corre → migración `000` |
| asyncpg conectando a `127.0.0.1:5432` | No existía `DATABASE_URL`; Pydantic cayó al default. `POSTGRES_*` no las lee la app |
| `SettingsError` en `cors_origins` | `list[str]` dispara `json.loads` en EnvSettingsSource, **antes** del validador |
| Healthcheck en silencio 5 min | Alembic colgado (lock); con `&&`, gunicorn nunca arrancaba |
| `Failed to parse start command` | El parser de Railway no es un shell: `>>>`, `(...)` y `;` lo rompen |
| Build del frontend bloqueado | `next@15.1.6` con CVE-2025-66478 (CRITICAL) y tres más |
| Login 500 | `REDIS_URL` inválida; `AuthService` recibe Redis como dependencia obligatoria |

## Entidades mencionadas
- [[entidades/pastrystock-manager]] — el sistema, ahora desplegado
- [[entidades/backend-pastrystock]] — `start.sh`, migración `000`, permisos de `static/`
- [[entidades/frontend-nextjs]] — `PasswordInput`, subida de Next a 15.1.11

## Conceptos relacionados
- [[conceptos/despliegue-en-paas-vs-docker-compose]] — qué deja de hacerse por ti
- [[conceptos/enums-postgres-alembic-vs-init-sql]] — por qué el esquema debe vivir en Alembic
- [[conceptos/arranque-de-contenedor-y-healthcheck]] — migraciones fuera del camino crítico
- [[conceptos/proteccion-csrf-bearer-vs-cookies]] — dónde está (y dónde no) la superficie CSRF
- [[conceptos/reproducir-el-contenedor-de-produccion-en-local]] — método de depuración
- [[conceptos/campo-contrasena-con-visibilidad]] — el componente y su accesibilidad
- [[conceptos/rate-limiting-redis]] — por qué el login depende de Redis
- [[conceptos/autenticacion-jwt-cookies-httponly]] — la cookie vive en Next, no en el backend

## Citas destacadas
> `/health` responde 200 aunque PostgreSQL esté mal configurado: el `lifespan` tolera el
> fallo del seed por diseño. Que un deploy pase el healthcheck **no** prueba que la app
> funcione.

## Notas de síntesis
El cuelgue de Alembic (T-RW-26) se resolvió reiniciando PostgreSQL, lo que apunta a una
sesión zombi con una transacción abierta: al matar Railway un contenedor, el backend de
Postgres sobrevive hasta que expira el keepalive TCP (~2 h), reteniendo sus locks. **La
causa raíz no está confirmada** y merece investigación si reaparece.
