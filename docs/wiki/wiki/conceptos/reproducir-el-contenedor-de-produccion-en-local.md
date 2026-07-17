---
title: "Reproducir el contenedor de producción en local"
tags: [depuracion, docker, despliegue, metodo, git]
source_count: 1
---

# Reproducir el contenedor de producción en local

## Definición
Depurar un despliegue contra el PaaS es un bucle de 5 minutos por intento, a ciegas y con
logs parciales. El mismo contenedor construido en local da la respuesta en segundos, con el
traceback entero. Es la diferencia entre teorizar y saber.

## Fuentes que lo mencionan
- [[fuentes/sesion-despliegue-railway-csrf-y-contrasenas]] — el método que cerró la sesión

## El detalle que importa: el contexto de build

El PaaS construye desde el **checkout de git**, no desde tu carpeta. Todo lo gitignorado
—`static/` en PastryStock— no existe allí. Construir desde el directorio local da una
imagen *distinta* a la de producción y oculta justo los fallos que buscas.

Para replicarlo de verdad:

```powershell
git archive HEAD:backend -o ctx.tar    # solo lo versionado
tar -x -f ctx.tar -C ctx
docker build --target production -t app-git ctx
```

## Comprobaciones útiles

| Qué quieres saber | Comando |
|---|---|
| ¿La app importa? (lo que hace gunicorn al arrancar) | `docker run --rm app-git python -c "import app.main"` |
| ¿Arranca y responde sin BD? | `docker run -d -p 8099:8000 app-git gunicorn …` + `curl /health` |
| ¿Cuánto tarda cada paso del arranque? | `Measure-Command { docker run --rm -e DATABASE_URL=… app-git alembic upgrade head }` |
| ¿Qué pasa con la BD inalcanzable? | `-e DATABASE_URL=postgresql+asyncpg://u:p@10.255.255.1:5432/db` |
| ¿Existe el binario que asumo? | `docker run --rm app-git timeout --version` |

## Perspectivas/decisiones

- **Verificar la premisa antes de pushear.** `NoDecode` parecía la solución idiomática al
  problema de `cors_origins`; comprobar el `__init__.py` del tag `v2.6.1` en GitHub reveló
  que no existe en esa versión. Habría sido otro deploy roto por `ImportError`.
- **Un Postgres desechable cuesta 10 segundos** y permite medir los seeds y las migraciones
  de verdad: `docker run -d --network X -e POSTGRES_PASSWORD=test postgres:16`.
- **Aislar antes de tocar los ficheros del usuario.** `pnpm install` sobre un bind-mount
  intentó borrar `node_modules`. Copiar `package.json` + lockfile a un directorio temporal
  y regenerar allí con `--lockfile-only` es seguro.
- **Los tiempos son evidencia.** Alembic no-op medido en 2.7 s en local convirtió los 5
  minutos de silencio en Railway de misterio en diagnóstico: no era lento, estaba
  bloqueado.

## Contradicciones detectadas
Ninguna. En este proyecto conviene además no ejecutar `next build` en el contenedor de
desarrollo (corrompe el `.next` del dev server): las validaciones del frontend se hacen en
una imagen desechable, como aquí.
