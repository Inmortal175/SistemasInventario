---
title: "Sesión: Frontend Next.js 15 y seed de admin"
date: 2026-07-08
source_url: ""
source_path: ""
type: sesion-desarrollo
tags: [frontend, nextjs, autenticacion, backend, seed, arquitectura]
---

# Sesión: Frontend Next.js 15 y seed de admin

## Resumen
Sesión de desarrollo en la que se construyó desde cero el frontend de PastryStock
Manager (Next.js 15 App Router + TypeScript + Tailwind) calcado al contrato de la API
FastAPI existente, y se creó un script de seed idempotente para el usuario
administrador inicial. El build se verificó exitosamente (11 rutas, type-check OK).

## Ideas clave
- **Auth JWT sin librería externa**: login vía OAuth2 password flow del backend; el
  token se guarda en **cookies httpOnly** (`pastry_token` + `pastry_user`) para que
  JavaScript del cliente nunca lo lea. Middleware protege rutas por presencia de cookie.
- **Lectura con Server Components, mutación con Server Actions**: los listados se
  obtienen server-side adjuntando el bearer desde la cookie; las altas/movimientos
  usan Server Actions con `useActionState` (React 19) — sin API routes intermedias.
- **Doble base URL**: `INTERNAL_API_URL` (red interna de Docker, `backend:8000`) para
  las llamadas desde el servidor; `NEXT_PUBLIC_API_URL` como fallback local.
- **RBAC reflejado en el cliente**: STAFF solo ve movimientos EXIT/WASTE; las altas de
  insumos/categorías/ubicaciones se ocultan y se protegen (redirect) para no-admin.
- **Seed idempotente**: crea el SUPERADMIN desde `settings.superadmin_email/password`;
  si el correo ya existe no lo duplica, y reactiva la cuenta si estaba inactiva.
- El empaquetado `output: "standalone"` falla en Windows local por symlinks (EPERM),
  pero funciona en el contenedor Linux; se añadió el escape `NEXT_DISABLE_STANDALONE`.

## Entidades mencionadas
- [[entidades/pastrystock-manager]] — proyecto sobre el que se trabajó
- [[entidades/frontend-nextjs]] — módulo construido en esta sesión
- [[entidades/script-seed-admin]] — utilidad de bootstrap creada

## Conceptos relacionados
- [[conceptos/autenticacion-jwt-cookies-httponly]] — estrategia de sesión aplicada
- [[conceptos/server-components-vs-server-actions]] — patrón de datos del App Router
- [[conceptos/rbac]] — control de acceso por rol, espejado en el frontend
- [[conceptos/seed-idempotente]] — patrón del script de bootstrap

## Citas destacadas
> "Lectura en Server Components (bearer desde cookie, red interna de Docker),
> mutaciones vía Server Actions con `useActionState`."

## Notas de síntesis
Primera fuente de la wiki. Establece el vocabulario base de arquitectura del proyecto.
Futuras sesiones sobre historial de movimientos o edición de insumos deberían enlazar
a [[conceptos/server-components-vs-server-actions]] y [[entidades/frontend-nextjs]].
