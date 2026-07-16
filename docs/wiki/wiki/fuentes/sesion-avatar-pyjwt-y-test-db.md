---
title: "Sesión: Avatar de perfil, migración a PyJWT y aislamiento de la BD de tests"
date: 2026-07-08
source_url: ""
source_path: ""
type: sesion-desarrollo
tags: [avatar, jwt, pyjwt, testing, base-datos, migraciones, backend, frontend]
---

# Sesión: Avatar de perfil, migración a PyJWT y aislamiento de la BD de tests

## Resumen
Tres frentes: (1) migración de `python-jose` (sin mantenimiento, usa `datetime.utcnow()`
deprecado) a **PyJWT**, eliminando las 98 advertencias de la suite; (2) completado de la
funcionalidad de **avatar de perfil** que estaba a medias y **rompía el login** (migración
003 sin aplicar); (3) **aislamiento definitivo de la BD de tests** para que `pytest` no
vuelva a borrar los datos de desarrollo.

## Ideas clave
- **PyJWT**: `app/core/security.py` ahora usa `import jwt` / `PyJWTError`; el JWT sigue
  llevando `iat` (época de sesión). `requirements.txt` reemplaza jose por `PyJWT==2.10.1`.
  Verificado: encode/decode, token inválido y expirado rechazados, sin DeprecationWarning.
- **Avatar**: ver [[conceptos/avatar-perfil-y-estaticos]]. La causa del login roto era la
  migración `003_add_avatar_url` sin aplicar (columna `avatar_url` inexistente → el SELECT
  del ORM fallaba). Se aplicó `alembic upgrade head`.
- **BD de tests**: ver [[conceptos/aislamiento-bd-tests]]. `scripts/setup_test_db.py`
  crea `pastry_test`; el conftest apunta ahí. Verificado: tras `pytest`, el superadmin de
  desarrollo sobrevive.

## Verificación realizada
- `pytest`: **89 passed**, cobertura **81.8%**, **0 warnings**.
- Avatar E2E: subida PNG→200 (backend y vía route handler del frontend), estático servido
  como image/png, tipo inválido→422, login refleja `avatar_url`.
- Aislamiento: superadmin de `pastry_inventory` intacto tras correr la suite.
- Frontend: `tsc` limpio, `build` OK (17 rutas), `/profile` muestra la sección de avatar.

## Entidades mencionadas
- [[entidades/backend-pastrystock]] — PyJWT, avatar, BD de tests
- [[entidades/frontend-nextjs]] — AvatarForm, route handler, avatar en sidebar

## Conceptos relacionados
- [[conceptos/avatar-perfil-y-estaticos]]
- [[conceptos/aislamiento-bd-tests]]
- [[conceptos/gestion-perfil-usuario]]
- [[conceptos/recuperacion-contrasenas]]

## Notas de síntesis
Con el aislamiento de la BD de tests queda cerrado el problema recurrente que borraba el
superadmin en cada corrida de `pytest`. Requisito operativo: correr una vez
`scripts/setup_test_db.py` (o tras añadir migraciones).
