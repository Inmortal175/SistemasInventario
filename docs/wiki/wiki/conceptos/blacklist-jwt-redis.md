---
title: "Blacklist de JWT en Redis (invalidación de sesión)"
tags: [seguridad, jwt, redis, sesiones, rbac]
source_count: 1
---

# Blacklist de JWT en Redis (invalidación de sesión)

## Definición
Mecanismo para invalidar la sesión de un usuario suspendido cuando se usan JWT stateless
(sin estado en servidor). Al suspender, se marca al usuario en una blacklist Redis y toda
petición posterior con su token se rechaza (HU-10-02).

## Implementación
- El JWT lleva `sub` = user_id (no hay `jti`), por lo que la blacklist es **por usuario**:
  clave `token:blacklist:{user_id}` con TTL = vida máxima del token
  (`access_token_expire_minutes × 60`).
- `UserService.suspend`: `is_active=false` en PostgreSQL + blacklist en Redis.
  `reactivate` borra la clave.
- `get_current_user` (dependencia) revisa `redis.exists(token_blacklist_key(sub))` tras
  decodificar el token; si existe → 401.
- Doble barrera: aunque Redis caiga (fail-open), el flag `is_active=false` en PostgreSQL
  también rechaza al usuario.

## Fuentes que lo mencionan
- [[fuentes/sesion-backend-completo-16-hu]] — verificado: 200 antes, 401 tras suspender

## Perspectivas/decisiones
La blacklist por user_id invalida todos los tokens vigentes del usuario a la vez, lo cual
es el comportamiento deseado en una suspensión. Complementa el JWT de
[[conceptos/autenticacion-jwt-cookies-httponly]].

## Contradicciones detectadas
Ninguna.
