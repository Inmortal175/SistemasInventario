---
title: "Script seed_admin"
type: herramienta
tags: [seed, bootstrap, backend, cli]
---

# Script seed_admin

## Descripción
Utilidad de bootstrap en `backend/scripts/seed_admin.py`. Crea el primer usuario con
privilegios (SUPERADMIN por defecto) a partir de `settings.superadmin_email` /
`superadmin_password`. Aplica el patrón [[conceptos/seed-idempotente]].

**Ejecución:**
```bash
docker-compose exec backend python scripts/seed_admin.py
docker-compose exec backend python scripts/seed_admin.py \
    --email jefe@pasteleria.com --password "Secreto@123" --role ADMIN
```

**Comportamiento:** si el correo ya existe, no duplica; si estaba inactivo, lo reactiva.
Usa `AsyncSessionLocal`, `UserRepository`, `hash_password` (bcrypt) y hace `engine.dispose()`
al final. Inserta la raíz del backend en `sys.path` para importar `app` desde cualquier cwd.

## Aparece en
- [[fuentes/sesion-frontend-nextjs-y-seed-admin]] — sesión de creación

## Relaciones
- [[entidades/pastrystock-manager]] — proyecto contenedor
- Necesario para el login del [[entidades/frontend-nextjs]] (no hay registro público)

## Notas
El backend no expone registro público: el primer usuario se crea con este script; los
demás (ADMIN / STAFF) se crean luego vía API desde una cuenta con privilegios.
