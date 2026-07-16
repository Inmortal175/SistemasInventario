---
title: "Gestión de perfil de usuario (self-service)"
tags: [usuarios, perfil, self-service, seguridad, ux]
source_count: 1
---

# Gestión de perfil de usuario (self-service)

## Definición
Cualquier usuario autenticado puede ver y editar su propio perfil: actualizar su nombre
visible y cambiar su contraseña conociendo la actual. Complementa la gestión por
SUPERADMIN (crear/suspender/reset) de [[conceptos/recuperacion-contrasenas]].

## Implementación
- **Backend** (en el router `/auth`, junto a `GET /auth/me`, para evitar el conflicto de
  rutas con `/{user_id}`):
  - `PATCH /api/v1/auth/me` — `{full_name}` → `UserService.update_own_profile`.
  - `PATCH /api/v1/auth/me/password` — `{current_password, new_password}` →
    `UserService.change_own_password`, que verifica la clave actual con `verify_password`
    (falla → `InvalidCredentialsError` 401) y NO invalida la sesión en curso.
- **Frontend**: página `/profile` (accesible desde el nombre en el sidebar) con
  `ProfileForm` y `ChangePasswordForm`. La actualización de nombre refresca la cookie de
  sesión (`updateSessionName`) para reflejarlo sin re-login.

## Fuentes que lo mencionan
- [[fuentes/sesion-perfil-y-cobertura-tests]] — implementación y verificación

## Perspectivas/decisiones
El cambio self-service (usuario que ya conoce su clave) no dispara la época de sesión,
a diferencia del reset por admin (posible cuenta comprometida). Coloca los endpoints en
`/auth/me` para no chocar con `/users/{user_id}` en el enrutado de FastAPI.

## Contradicciones detectadas
Ninguna.
