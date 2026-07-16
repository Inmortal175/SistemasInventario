---
title: "Sesión: Perfil de usuario, corrección de tests y cobertura ≥80%"
date: 2026-07-08
source_url: ""
source_path: ""
type: sesion-desarrollo
tags: [usuarios, perfil, testing, cobertura, integracion, backend, frontend]
---

# Sesión: Perfil de usuario, corrección de tests y cobertura ≥80%

## Resumen
El usuario corrió `pytest -v` completo y detectó: un test de login desactualizado y la
cobertura bajo el umbral (76% < 80%). Además pidió gestión de perfil de usuario. Se
corrigió el test, se añadió el módulo de perfil (backend + frontend) y se amplió la suite
de integración para los módulos avanzados, llevando la cobertura a **81.8%** con 88 tests
en verde.

## Ideas clave
- **Test obsoleto**: `test_login_wrong_password` esperaba 403; el login ahora responde
  401/`INVALID_CREDENTIALS` (SC-HU04-02). Se actualizó la aserción, no el código.
- **Perfil self-service**: [[conceptos/gestion-perfil-usuario]] — `PATCH /auth/me` y
  `PATCH /auth/me/password`; página `/profile` enlazada desde el nombre en el sidebar.
- **Cobertura**: nuevo `tests/integration/test_advanced_api.py` (16 casos) que ejercita
  lotes/FIFO, valorización, conciliación, dashboard, usuarios (ciclo completo), reportes,
  producción (simulate/produce/rollback) y perfil. Los tests de integración cubren de una
  vez endpoint→servicio→repositorio, que era el grueso del código sin cubrir.
- Se añadieron `recipe_items, recipes, supply_batches` al TRUNCATE del conftest de integración.

## Verificación realizada
- `docker compose exec backend pytest`: **88 passed**, cobertura **81.8%** (≥80%).
- Perfil E2E: cambio de nombre 200; clave actual mala→401, correcta→200 y login con la nueva.
- Frontend: `/profile` renderiza y el nombre del sidebar enlaza a él; `tsc` y `build` OK (16 rutas).

## Entidades mencionadas
- [[entidades/backend-pastrystock]] — endpoints de perfil y suite de integración
- [[entidades/frontend-nextjs]] — página /profile

## Conceptos relacionados
- [[conceptos/gestion-perfil-usuario]]
- [[conceptos/recuperacion-contrasenas]]

## Notas de síntesis
**Confirmado por tercera vez**: correr la suite de integración (`pytest`, que incluye
`tests/integration`) TRUNCA la BD de desarrollo compartida y borra el superadmin sembrado.
Tras cada corrida hay que re-sembrar con `scripts/seed_admin.py`. Pendiente recomendado:
apuntar la integración a una BD desechable (servicio Postgres de test separado) para no
tocar los datos de desarrollo.
