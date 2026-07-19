---
title: "Script reset_system.py"
type: herramienta
tags: [reset, mantenimiento, redis, truncate, operaciones, demo]
---

# Script `reset_system.py`

## Descripción
Deja la base limpia antes de un `seed_demo.py` nuevo (demos, QA). Vive en
`backend/scripts/reset_system.py`. Es la contraparte destructiva que
[[entidades/script-seed-demo]] deliberadamente no ofrecía, porque `movement_history` es
inmutable *en el flujo de la app* — pero un reset de mantenimiento sí puede truncarlo.

```bash
python scripts/reset_system.py            # dry-run: solo reporta conteos
python scripts/reset_system.py --yes      # ejecuta el borrado
python scripts/reset_system.py --yes --keep-staff   # conserva usuarios STAFF
python scripts/reset_system.py --yes --keep-cache   # no toca Redis
```

## Qué borra y qué conserva
- **Borra** los datos de negocio con un solo `TRUNCATE ... RESTART IDENTITY CASCADE`:
  `production_run_items`, `production_runs`, `movement_history`, `recipe_items`, `recipes`,
  `supply_batches`, `supply_items`, `locations`, `dynamic_categories`. El `CASCADE` resuelve
  el orden de las FKs `RESTRICT` sin tener que borrar hija-a-padre a mano.
- **Conserva** usuarios ADMIN/SUPERADMIN y `system_settings` (identidad visual). Los STAFF se
  eliminan salvo `--keep-staff`.
- **Purga Redis** de forma selectiva: `categories:*`, `category:*`, `supplies:page:*`,
  `dashboard:kpis`, `settings:system`. No usa `FLUSHDB` para no tumbar rate-limits ni
  blacklists de tokens.

## Salvaguardas
- **Dry-run por defecto**: sin `--yes` solo imprime los conteos que borraría.
- **Aborta si no quedaría ningún admin** (evita dejar el sistema sin acceso).
- `users` y `system_settings` no están en la lista de `TRUNCATE` a propósito: son
  referenciadas, no se truncan; el `CASCADE` no las alcanza.

## Aparece en
- [[fuentes/sesion-reset-sistema-y-cache-first-seed]] — creación y motivación

## Relaciones
- [[entidades/backend-pastrystock]] — usa sus modelos, tablas y llaves de caché
- [[entidades/script-seed-demo]] — se corre *después* del reset
- Aplica [[conceptos/invalidacion-cache-al-sembrar-directo-a-db]]
- Preserva el modelo de [[conceptos/rbac]] (conserva admins)

## Notas
El flujo operativo completo en Railway es: `railway ssh --service backend` →
`reset_system.py --yes` → `seed_demo.py`.
