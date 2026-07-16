---
title: "Server Components vs Server Actions"
tags: [nextjs, app-router, react, patrones-datos]
source_count: 1
---

# Server Components vs Server Actions

## Definición
Patrón de flujo de datos del App Router de Next.js 15 usado en el proyecto:
- **Server Components** para *lectura*: se ejecutan en el servidor, obtienen datos
  directamente de la API (adjuntando el bearer desde la cookie) y renderizan HTML sin
  exponer el token ni requerir API routes intermedias.
- **Server Actions** para *mutación*: funciones `"use server"` invocadas desde formularios
  cliente con `useActionState` (React 19); validan, llaman a la API, revalidan caché con
  `revalidatePath` y devuelven un `FormState` para feedback.

## Fuentes que lo mencionan
- [[fuentes/sesion-frontend-nextjs-y-seed-admin]] — patrón base del frontend

## Perspectivas/decisiones
- Lecturas centralizadas en `src/lib/queries.ts`; mutaciones en `src/app/actions/*`.
- `redirect()` en Server Actions (p. ej. login) se llama **fuera** del try/catch para no
  capturar su señal interna (`NEXT_REDIRECT`).
- Estado de formularios unificado con `FormState` (`idle | success | error`) en `lib/form.ts`.
- Componentes cliente mínimos (SubmitButton con `useFormStatus`, FormMessage) — el resto
  es server-first.

## Contradicciones detectadas
Ninguna. Es el enfoque idiomático de Next 15; evita duplicar lógica en el cliente.
