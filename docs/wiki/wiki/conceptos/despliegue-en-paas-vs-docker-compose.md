---
title: "Despliegue en PaaS vs docker-compose"
tags: [despliegue, railway, docker, configuracion, paas]
source_count: 1
---

# Despliegue en PaaS vs docker-compose

## Definición
En un PaaS (Railway, Render, Fly) desaparece el `docker-compose.yml`, y con él todo el
trabajo invisible que hacía. Cada cosa que compose resolvía por ti pasa a ser tu
responsabilidad — y su ausencia no se manifiesta como un error claro, sino como un
arranque que muere en silencio.

## Fuentes que lo mencionan
- [[fuentes/sesion-despliegue-railway-csrf-y-contrasenas]] — siete fallos, todos de esta familia

## Qué deja de hacerse solo

| Lo hacía compose | En el PaaS |
|---|---|
| Construir `DATABASE_URL`/`REDIS_URL` desde `POSTGRES_*`/`REDIS_PASSWORD` | Nadie. Hay que definirlas enteras y a mano |
| Ejecutar `sql/init.sql` en `/docker-entrypoint-initdb.d` | Nunca se ejecuta. El esquema debe vivir en Alembic |
| Montar el código como volumen (incluidos ficheros gitignorados) | El contexto es el checkout de git: lo ignorado **no existe** |
| Resolver `backend:8000` por DNS interno | Dominio privado del servicio y el puerto que inyecta el PaaS |
| Fijar el puerto | El PaaS inyecta `PORT`; hay que respetarlo o fijarlo explícitamente |

## Perspectivas/decisiones

- **`.env.example` no es la lista de variables del PaaS.** Es la lista de las que necesita
  *compose*. En PastryStock, `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD`,
  `REDIS_PASSWORD` y `NEXTAUTH_SECRET` (esta última ni siquiera se usa: no hay `next-auth`)
  se copiaron a Railway sin que la app leyera ninguna. La app lee `DATABASE_URL` y
  `REDIS_URL`, que compose fabricaba en las líneas 56-58 del `docker-compose.yml`.
- **El driver va en la URL.** Railway entrega `postgresql://…`; SQLAlchemy async exige
  `postgresql+asyncpg://…`. Con la forma corta, `create_async_engine` revienta al importar
  y el proceso muere antes de escuchar.
- **Las referencias `${{Servicio.VAR}}` hacen match exacto por nombre.** Si el servicio no
  se llama igual, la referencia no resuelve y el PaaS **deja la variable sin definir** — que
  se manifiesta como el default del código, no como un error. Así apareció el
  `Connect call failed ('127.0.0.1', 5432)`: era el default de `config.py`.
- **`Root Directory` es obligatorio en monorepos.** Sin él, el PaaS analiza la raíz, no
  encuentra cómo construir y ni siquiera llega a ver `backend/railway.json`.
- **El filesystem es efímero.** Lo que se sube en runtime (avatares, logo) desaparece en
  cada redeploy salvo que se monte un Volume. Ver [[conceptos/avatar-perfil-y-estaticos]].

## Contradicciones detectadas
Ninguna. Complementa a [[conceptos/hot-reload-docker-windows]]: ambos son casos de que el
entorno de ejecución (Windows, PaaS) rompe supuestos del entorno de desarrollo.
