---
title: "Protección CSRF: Bearer vs cookies"
tags: [seguridad, csrf, autenticacion, jwt, nextjs, fastapi]
source_count: 1
---

# Protección CSRF: Bearer vs cookies

## Definición
CSRF explota las **credenciales ambientales**: cualquier cosa que el navegador adjunte
automáticamente a una petición cross-site. En la práctica, cookies. Un token que la
aplicación tiene que poner a mano en una cabecera no es ambiental — y por tanto no es
explotable por CSRF.

De ahí la regla: **la superficie CSRF está donde vive la cookie**, no donde vive la sesión.

## Fuentes que lo mencionan
- [[fuentes/sesion-despliegue-railway-csrf-y-contrasenas]] — auditoría de la arquitectura

## La arquitectura de PastryStock

```
Navegador  --cookie httpOnly (pastry_token)-->  Next.js (servidor)
Next.js    --Authorization: Bearer <jwt>    -->  FastAPI
```

La cookie **nunca llega al backend**. El navegador jamás habla directamente con FastAPI.

## Perspectivas/decisiones

**El backend no tiene superficie CSRF.** `core/dependencies.py:22` usa
`OAuth2PasswordBearer`: la autenticación es exclusivamente por cabecera `Authorization`.
Un sitio atacante no puede hacer que el navegador de la víctima añada esa cabecera. Que no
exista una sola línea de código anti-CSRF en el backend **no es una carencia**: es la
consecuencia correcta de autenticar con Bearer. Añadir tokens CSRF ahí sería ceremonia sin
amenaza.

**La superficie real es Next.js**, y está cubierta por dos capas independientes:

1. **`sameSite: "lax"`** (`lib/session.ts:23`) — el navegador no adjunta la cookie en
   peticiones cross-site POST/PUT/DELETE. Esto solo ya bloquea el CSRF clásico contra los
   tres route handlers POST (`/api/profile/avatar`, `/api/settings/logo`,
   `/api/settings/login-background/[device]`).
2. **Server Actions** — Next.js compara `Origin` contra `Host` y rechaza los que no
   coinciden. Todos los formularios (login, alta de usuario, cambio de contraseña) usan
   actions, así que heredan esa protección de fábrica.

Además: `httpOnly` (inaccesible desde JS, mitiga el robo por XSS) y `secure` en producción.

**El único GET con cookie no es un riesgo.** `/api/reports/export` es de solo lectura. Con
`sameSite=lax` una navegación top-level sí lleva la cookie, pero la respuesta va al
navegador de la víctima y el atacante no puede leerla (sin CORS). No hay cambio de estado
→ no hay CSRF.

## Veredicto
**Protegido, pero de forma implícita.** La seguridad depende de dos comportamientos por
defecto (el `sameSite=lax` y la verificación de origen de las actions), no de código
explícito. Funciona, pero nada en el repositorio lo *declara*, así que un refactor podría
retirarlo sin que salte ninguna alarma — de ahí esta página.

**Mejora opcional (T-SEC-02):** validar `Origin` explícitamente en los tres route handlers
POST, que son los únicos endpoints con cookie que mutan estado y **no** están cubiertos por
la protección automática de las Server Actions.

## Contradicciones detectadas
Ninguna. Extiende [[conceptos/autenticacion-jwt-cookies-httponly]], que documenta el porqué
de la cookie pero no analizaba el vector CSRF.
