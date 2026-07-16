---
title: "Rate limiting de login con Redis"
tags: [seguridad, rate-limiting, redis, autenticacion]
source_count: 1
---

# Rate limiting de login con Redis

## Definición
Protección contra fuerza bruta en el login: cuenta los intentos fallidos por IP y bloquea
la IP tras superar un umbral (HU-04-02).

## Implementación
- Claves Redis: `login:rate_limit:{ip}` (contador con ventana) y `login:blocked:{ip}`
  (marca de bloqueo con TTL).
- Config: `login_max_attempts=5`, `login_window_seconds=900` (15 min),
  `login_block_seconds=900`.
- `AuthService.login(client_ip)`:
  1. Si la IP está bloqueada (TTL>0) → `RateLimitExceededError` (HTTP 429 con header
     `Retry-After`) antes de tocar la BD.
  2. En fallo, `INCR` del contador; el primer fallo fija `EXPIRE` de la ventana; al
     llegar a 5 fija la clave de bloqueo.
  3. En login correcto, borra ambos contadores.
- La IP se toma de `X-Forwarded-For` (primer valor) o `request.client.host`.
- Degradación: si Redis no responde, el rate limiting se omite (fail-open) sin romper el login.

## Fuentes que lo mencionan
- [[fuentes/sesion-backend-completo-16-hu]] — verificado: 6º intento = 429, Retry-After 900

## Perspectivas/decisiones
Credenciales inválidas devuelven 401 (`InvalidCredentialsError`), corrigiendo el 403
previo para cumplir SC-HU04-02. Relacionado con [[conceptos/blacklist-jwt-redis]] y [[conceptos/rbac]].

## Contradicciones detectadas
Ninguna.
