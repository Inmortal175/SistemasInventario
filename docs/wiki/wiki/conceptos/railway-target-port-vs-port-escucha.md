---
title: "Railway: Target Port vs. puerto de escucha ($PORT)"
tags: [railway, despliegue, redes, puertos, bad-gateway]
source_count: 1
---

# Railway: Target Port vs. puerto de escucha (`$PORT`)

## Definición
En Railway el puerto no se "fija" como en `docker-compose`. Railway inyecta la variable `PORT`
y la app debe escuchar en ella; el proxy público expone todo por **HTTPS/443** (sin puerto en la
URL). El **Target Port** del dominio debe coincidir con el puerto donde la app realmente escucha.
Un 502 Bad Gateway con la app arrancando bien = el proxy toca un puerto donde no hay nadie.

## Síntoma
Bad Gateway en las URLs `*.up.railway.app` mientras los Deploy Logs muestran la app sana:
`Listening at: http://0.0.0.0:8080` y `Application startup complete`. No es error de código.

## Reglas
- **No fijar `PORT` a mano**: dejar que Railway la inyecte y autodetecte el Target Port. Si se
  fija, el Target Port debe ser ese mismo número.
- El código ya respeta `$PORT`: `start.sh` hace `--bind 0.0.0.0:${PORT:-8000}`; Next standalone
  (`node server.js`) escucha en `$PORT` con `HOSTNAME=0.0.0.0`. Los `8000`/`3000` son solo
  fallbacks de `docker-compose` local, no "el puerto de Railway".
- **No usar `PORT=80` para el frontend**: el contenedor corre como usuario no-root (`nextjs`,
  uid 1001) y no puede enlazar puertos <1024 → crashea → Bad Gateway.
- Cambiar el Target Port **no requiere redeploy**: el proxy re-enruta al instante.

## Perspectivas/decisiones
El caso real: ambas apps escuchaban en 8080 (por un `PORT` puesto a mano), pero el Target Port
del proxy no coincidía. La solución robusta es borrar el `PORT` manual y dejar la autodetección,
para que el número de escucha y el de ruteo nunca se desincronicen.

## Contradicciones detectadas
Ninguna. Extiende a [[conceptos/despliegue-en-paas-vs-docker-compose]]: otra cosa que
`docker-compose` mapeaba por ti (`ports: "8000:8000"`) y en un PaaS gestiona la plataforma.

## Fuentes que lo mencionan
- [[fuentes/sesion-reset-sistema-y-cache-first-seed]] — diagnóstico del 502
