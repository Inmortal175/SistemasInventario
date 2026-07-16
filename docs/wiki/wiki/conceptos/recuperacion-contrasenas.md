---
title: "Recuperación de contraseñas y época de sesión"
tags: [seguridad, contrasenas, jwt, recuperacion, rbac]
source_count: 1
---

# Recuperación de contraseñas y época de sesión

## Definición
Mecanismo para restablecer credenciales sin infraestructura de correo. Dos vías según
quién la pierde, más una defensa de sesión que invalida los tokens previos al cambio.

## Vías de recuperación
1. **Restablecimiento por SUPERADMIN** (usuario pierde su clave):
   `PATCH /api/v1/users/{id}/password` con `{new_password}`. En el frontend, botón
   "Contraseña" por fila en la página de Usuarios (componente `ResetPassword`).
2. **CLI en el servidor** (el propio SUPERADMIN pierde su clave — no hay nadie por encima):
   `scripts/reset_password.py --email … [--password …]`. Si se omite la clave, genera una
   temporal segura y la imprime una vez. Equivale a `changepassword` de Django.
3. **Cambio self-service** (el usuario conoce su clave y quiere cambiarla):
   `PATCH /api/v1/auth/me/password` con `{current_password, new_password}` — verifica la
   actual. NO invalida la sesión en curso (bajo riesgo). Ver [[conceptos/gestion-perfil-usuario]].

## Época de sesión (session epoch)
Al restablecer una contraseña se **invalidan los tokens JWT emitidos antes del cambio**,
pero se permite el re-login inmediato — algo que la [[conceptos/blacklist-jwt-redis]] por
`user_id` (usada en la suspensión) NO permite, porque bloquearía también el token nuevo.

- El JWT incluye `iat` (issued-at).
- Al resetear se escribe `token:valid_from:{user_id}` = timestamp actual (TTL = vida del token).
- `get_current_user` rechaza si `token.iat < valid_from`.
- El token nuevo (login posterior) tiene `iat > valid_from` → válido. `reactivate` limpia la marca.
- Granularidad de segundos: un token emitido en el mismo segundo del reset podría no
  rechazarse (colisión de segundo, irrelevante en el flujo humano real).

## Fuentes que lo mencionan
- [[fuentes/sesion-recuperacion-y-ux-modulos]] — implementación y verificación E2E

## Perspectivas/decisiones
Sin SMTP no hay self-service seguro por correo; la vía admin + CLI es la opción correcta
para el MVP. Un flujo self-service con token de un solo uso requeriría añadir email.
El reset invalida sesiones activas (defensa ante robo de token previo al cambio).

## Contradicciones detectadas
Ninguna. Coexiste con la blacklist total de la suspensión ([[conceptos/rbac]], HU-10-02).
