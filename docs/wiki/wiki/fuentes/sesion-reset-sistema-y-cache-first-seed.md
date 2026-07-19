---
title: "Sesión: reset del sistema y cache-first en el seed (Railway)"
date: 2026-07-19
source_url: ""
source_path: ""
type: sesion
tags: [railway, despliegue, redis, cache-first, seed, reset, operaciones]
---

# Sesión: reset del sistema y cache-first en el seed (Railway)

## Resumen
Tras el despliegue en Railway, el `seed_demo.py` se corrió dentro del contenedor pero el
frontend seguía mostrando todo vacío (sin insumos, categorías, productos ni movimientos).
La causa no fue el seed: fue la **caché cache-first de Redis** sirviendo listas vacías
cacheadas antes de sembrar. Se creó un script de reset del sistema y se hizo al `seed_demo.py`
auto-suficiente invalidando esas cachés al terminar. Commit `8ea052d` en `main`.

## Ideas clave
- **El seed escribe directo a PostgreSQL y no toca Redis.** La app sirve varios listados
  cache-first (`categories:active:all`, `categories:names:active`, `supplies:page:*`,
  `dashboard:kpis`, `settings:system`). Si el frontend consultó esos endpoints *antes* de
  sembrar, cacheó listas vacías y siguió mostrándolas aunque la DB ya tuviera datos.
- **Diagnóstico sin borrar nada**: correr solo el seed mejorado (que ahora invalida caché) y
  ver si aparecen los datos. Si aparecen, era 100% caché y ni se necesita el reset.
- **Nuevo `scripts/reset_system.py`**: borra los datos de negocio, conserva admins y
  `system_settings`, y purga las cachés. `TRUNCATE ... CASCADE` resuelve el orden de las FKs
  `RESTRICT`. Dry-run por defecto; exige `--yes`. Aborta si no quedaría ningún admin.
- **Purga selectiva de Redis, no FLUSHDB**: se borran solo las llaves de datos de demo
  (`categories:*`, `category:*`, `supplies:page:*`, `dashboard:kpis`, `settings:system`) para
  no tumbar rate-limits de login ni blacklists de tokens.
- **Railway y el puerto**: el 502 Bad Gateway previo no era del código — ambas apps arrancaban
  bien escuchando en `$PORT` (8080), pero el **Target Port** del proxy no coincidía. En Railway
  el puerto público es siempre 443; lo que importa es que el Target Port = puerto donde escucha
  la app. Fijar `PORT=80` rompe el frontend porque corre como usuario no-root.

## Entidades mencionadas
- [[entidades/pastrystock-manager]] — el sistema desplegado
- [[entidades/script-reset-system]] — herramienta nueva creada en esta sesión
- [[entidades/script-seed-demo]] — mejorado para invalidar caché
- [[entidades/backend-pastrystock]] — dueño de los modelos y las llaves de caché

## Conceptos relacionados
- [[conceptos/invalidacion-cache-al-sembrar-directo-a-db]] — la lección central
- [[conceptos/railway-target-port-vs-port-escucha]] — el 502 y el puerto
- [[conceptos/cache-first-paginacion]] — el lado de lectura que aquí quedó stale
- [[conceptos/seed-idempotente]] — el seed sigue siendo reejecutable

## Notas de síntesis
Refuerza a [[conceptos/cache-obsoleta-tras-cambio-de-schema]]: Redis vuelve a ser el sospechoso
cuando "la DB tiene datos pero la app no los muestra". Antes fue una entrada vieja tras migrar;
ahora, listas vacías cacheadas antes de sembrar. La regla emergente: **toda escritura directa a
la DB que salte la capa de servicio debe invalidar las llaves cache-first afectadas.**
