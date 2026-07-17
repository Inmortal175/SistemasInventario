---
title: "ENUMs de PostgreSQL: Alembic vs init.sql"
tags: [alembic, postgresql, migraciones, enums, despliegue]
source_count: 1
---

# ENUMs de PostgreSQL: Alembic vs init.sql

## Definición
Los tipos ENUM nativos de PostgreSQL son objetos del esquema, igual que las tablas. Si se
crean fuera de Alembic, el esquema deja de ser reproducible: funciona donde ese script
corre y falla donde no.

## Fuentes que lo mencionan
- [[fuentes/sesion-despliegue-railway-csrf-y-contrasenas]] — el fallo y la migración `000`

## El problema
PastryStock definía sus cuatro ENUMs (`user_role`, `unit_measure`, `movement_type`,
`location_type`) en `backend/sql/init.sql`, y las migraciones los referenciaban con
`create_type=False` para no duplicarlos:

```python
postgresql.ENUM("SUPERADMIN", "ADMIN", "STAFF", name="user_role", create_type=False)
```

Eso funciona en desarrollo **solo** porque `docker-compose` monta el script en
`/docker-entrypoint-initdb.d`, donde PostgreSQL lo ejecuta en su primer arranque. Un
PostgreSQL gestionado nunca ejecuta ese fichero: la migración `001` fallaba con
`type "user_role" does not exist`.

## Perspectivas/decisiones
- **El esquema completo debe vivir en Alembic.** Se añadió la migración `000` (nueva raíz,
  con `001` encadenada detrás) que crea los ENUMs y la extensión `uuid-ossp`.
- **Idempotencia con `DO $$ … EXCEPTION WHEN duplicate_object`**: en bases donde `init.sql`
  ya los creó, la `000` es un no-op. No hace falta tocar los entornos existentes ni la BD
  de desarrollo, que ya estaba en `008`.
- **`init.sql` se conserva** por compatibilidad con el primer arranque de compose, pero ya
  no es la fuente de verdad: es un atajo redundante.
- Verificado sobre una base virgen sin `init.sql`: `000 → 008` en 3.1 s.

## Contradicciones detectadas
El `CLAUDE.md` raíz del proyecto todavía afirma que los ENUMs "están definidos en
`backend/sql/init.sql` (ejecutado en primer boot de PostgreSQL)". Sigue siendo cierto para
compose, pero **ya no es la fuente de verdad del esquema**: desde la migración `000`, ese
papel es de Alembic. Conviene actualizar esa sección.
