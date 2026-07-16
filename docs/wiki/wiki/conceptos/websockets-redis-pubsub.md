---
title: "Alertas en tiempo real: WebSockets + Redis Pub/Sub"
tags: [websockets, redis, pubsub, tiempo-real, alertas]
source_count: 1
---

# Alertas en tiempo real: WebSockets + Redis Pub/Sub

## Definición
Difusión instantánea de alertas (stock crítico, vencimiento) al dashboard sin polling,
combinando WebSockets (FastAPI) con Redis Pub/Sub como bus de eventos (HU-14).

## Arquitectura
1. Un movimiento que baja del mínimo publica en el canal Redis `alerts:low_stock`
   (o `alerts:expiration_critical` para vencimientos).
2. Un **listener en background** (`redis_alert_listener`, arrancado en el lifespan de la
   app) está suscrito a ambos canales.
3. Al recibir un evento, el listener lo retransmite vía `ConnectionManager.broadcast` a
   todas las conexiones WebSocket del grupo de administradores.
4. El endpoint `WS /api/v1/ws/notifications?token={jwt}` valida el JWT en el handshake,
   comprueba rol ADMIN/SUPERADMIN y responde con `connection_established`.

## Detalles
- `ConnectionManager` mantiene las conexiones en memoria agrupadas por rol, con limpieza
  de conexiones muertas.
- El listener reintenta ante caídas de Redis (sleep 5s) sin tumbar el proceso; se cancela
  limpiamente en el shutdown.
- Desacopla al productor (servicio de negocio) del consumidor (WS): el negocio solo
  publica en Redis, no conoce las conexiones.

## Fuentes que lo mencionan
- [[fuentes/sesion-backend-completo-16-hu]] — verificado E2E: consumo → alerta → WS

## Perspectivas/decisiones
Redis Pub/Sub (en vez de broadcast directo) permite escalar a múltiples workers/instancias
de FastAPI: cualquier worker que publique llega a los WS de cualquier otro worker suscrito.

## Contradicciones detectadas
Ninguna.
