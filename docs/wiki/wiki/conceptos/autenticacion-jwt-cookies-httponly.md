---
title: "Autenticación JWT con cookies httpOnly"
tags: [autenticacion, seguridad, jwt, cookies, nextjs]
source_count: 1
---

# Autenticación JWT con cookies httpOnly

## Definición
Estrategia de sesión donde el JWT emitido por el backend (OAuth2 password flow) se
almacena en cookies **httpOnly** en lugar de `localStorage`. Al ser httpOnly, el token
no es accesible desde JavaScript del cliente, mitigando robo por XSS.

## Fuentes que lo mencionan
- [[fuentes/sesion-frontend-nextjs-y-seed-admin]] — implementación en el frontend

## Perspectivas/decisiones
- Dos cookies: `pastry_token` (el JWT) y `pastry_user` (id, nombre, rol en JSON) — ambas
  httpOnly, `sameSite=lax`, `secure` en producción, `maxAge` = expiración del token.
- El token se lee server-side (`getToken`) y se adjunta como `Authorization: Bearer` en
  los fetch a la API; nunca viaja al bundle del cliente.
- `middleware.ts` protege rutas por presencia de la cookie y redirige: sin token →
  `/login`; con token en ruta pública → `/dashboard`.
- Se evitó NextAuth para reducir complejidad en el MVP, pese a existir `NEXTAUTH_SECRET`
  en el compose.

## Contradicciones detectadas
Ninguna por ahora. Limitación conocida: el middleware valida presencia, no vigencia del
token; si expira, el backend responde 401 y la página lo maneja con su `error.tsx`.
