---
title: "Arranque de contenedor y healthcheck"
tags: [despliegue, docker, healthcheck, alembic, gunicorn, observabilidad]
source_count: 1
---

# Arranque de contenedor y healthcheck

## Definición
El comando de arranque de un contenedor en producción es un camino crítico: todo lo que
ocurra antes de que el servidor escuche consume la ventana del healthcheck. Si algo ahí se
cuelga, la plataforma mata el contenedor **sin ningún error en los logs**, porque nada ha
fallado — simplemente nadie ha llegado a hablar.

## Fuentes que lo mencionan
- [[fuentes/sesion-despliegue-railway-csrf-y-contrasenas]] — cinco minutos de silencio por deploy

## El antipatrón

```
alembic upgrade head && seed_admin.py && seed_demo.py && gunicorn …
```

Tres problemas:
1. **`&&` encadena**: si Alembic se cuelga esperando un lock, gunicorn nunca arranca. No
   hay traceback, solo silencio hasta que expira el healthcheck.
2. **Los seeds son silenciosos hasta terminar**: mientras corren no imprimen nada, así que
   un cuelgue ahí es indistinguible de uno en Alembic.
3. **Cada script levanta un intérprete que importa la app entera** y abre su propio engine,
   en serie, antes de servir la primera petición.

## El patrón

```sh
if timeout 90 alembic upgrade head; then
    echo "==> Migraciones al día."
else
    echo "!!! ALEMBIC FALLO O SUPERO LOS 90s — la app arranca igual."
fi
exec gunicorn app.main:app --bind "0.0.0.0:${PORT:-8000}" --log-level info
```

- **`timeout` + sin `set -e`**: un fallo de migración se anuncia, no secuestra el deploy.
- **La app arranca igual.** Es preferible una app en pie con el esquema desactualizado que
  un contenedor muerto: la primera se diagnostica, la segunda no.
- **`exec`** para que gunicorn sea PID 1 y reciba las señales de parada.

## Perspectivas/decisiones
- **Los seeds salieron del arranque.** `seed_admin` era además redundante: el `lifespan` de
  `main.py` ya llama a `create_initial_superadmin()`. Los datos demo se siembran a mano con
  `railway run python scripts/seed_demo.py`.
- **La lógica vive en `start.sh`, no en el `startCommand`.** El parser de Railway no es un
  shell completo: rechaza `>>>` (lo lee como redirección), paréntesis y `;`. `sh start.sh`
  son tres tokens que ningún parser rompe. Requiere `.gitattributes` con `*.sh text eol=lf`:
  en Windows con `core.autocrlf=true`, un CRLF colado rompe el script en Linux.
- **Un healthcheck que pasa no prueba que la app funcione.** `/health` en PastryStock
  devuelve 200 aunque PostgreSQL y Redis estén caídos, porque el `lifespan` tolera esos
  fallos a propósito. Es un *liveness check*, no un *readiness check*. La verificación real
  es `/docs` y un login.

## Contradicciones detectadas
Ninguna.
