---
title: "Sesión: Recuperación de contraseñas y UX explicativa de módulos"
date: 2026-07-08
source_url: ""
source_path: ""
type: sesion-desarrollo
tags: [seguridad, contrasenas, jwt, ux, frontend, backend]
---

# Sesión: Recuperación de contraseñas y UX explicativa de módulos

## Resumen
A partir de dos observaciones del usuario se añadieron: (1) un medio de recuperación de
contraseñas —el SUPERADMIN no podía restablecer claves y nadie podía recuperar la suya—,
y (2) explicaciones breves en cada módulo para hacer la UI autoexplicativa.

## Ideas clave
- **Reset por SUPERADMIN**: endpoint `PATCH /users/{id}/password` + botón "Contraseña"
  por fila en Usuarios. Ver [[conceptos/recuperacion-contrasenas]].
- **Reset del propio SUPERADMIN**: script `scripts/reset_password.py` (CLI en servidor),
  genera clave temporal si no se pasa una.
- **Época de sesión**: se agregó `iat` al JWT y la clave `token:valid_from:{user_id}`;
  al resetear se invalidan los tokens previos pero se permite el re-login inmediato.
  Corrige un bug propio: la primera versión usaba la blacklist total y dejaba al usuario
  bloqueado 60 min tras el reset.
- **UX**: componente `InfoBanner` con un texto breve al inicio de cada módulo
  (dashboard, insumos, movimientos, producción, categorías, ubicaciones, reportes, usuarios).

## Verificación realizada
- Backend E2E: clave vieja→200, reset→200, token viejo→401 (tras cruzar frontera de
  segundo), re-login con clave nueva→200, token nuevo→200, STAFF intentando resetear→403.
- 50 tests unitarios en verde; `tsc --noEmit` limpio; `next build` OK (15 rutas).
- Frontend: botón "Contraseña" e InfoBanner presentes en las 8 páginas de módulo.

## Entidades mencionadas
- [[entidades/backend-pastrystock]] — endpoint y script nuevos
- [[entidades/frontend-nextjs]] — ResetPassword e InfoBanner

## Conceptos relacionados
- [[conceptos/recuperacion-contrasenas]]
- [[conceptos/blacklist-jwt-redis]]
- [[conceptos/rbac]]

## Notas de síntesis
La incidencia de la BD truncada por `pytest tests/integration` (sesión anterior) volvió a
requerir re-sembrar el superadmin durante las pruebas. Refuerza la recomendación de aislar
la BD de integración de la de desarrollo.
