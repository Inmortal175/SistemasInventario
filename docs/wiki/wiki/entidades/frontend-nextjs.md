---
title: "Frontend Next.js"
type: modulo
tags: [frontend, nextjs, typescript, tailwind, app-router]
---

# Frontend Next.js

## Descripción
Capa de presentación de [[entidades/pastrystock-manager]]. Next.js 15 (App Router) +
TypeScript + Tailwind CSS 3.4, con alias `@/*` → `src/*`.

**Estructura relevante:**
- `src/lib/` — `types.ts` (espejo de schemas Pydantic), `api.ts` (fetch server-only con
  bearer), `session.ts` (cookies httpOnly), `queries.ts` (lecturas), `labels.ts`
  (etiquetas en español y helpers: formatMoney/Date/DateTime), `form.ts`.
- `src/app/actions/` — Server Actions: auth, categories, locations, supplies, movements,
  production, batches (lote/FIFO/conciliación), users.
- `src/app/(dashboard)/` — layout con sidebar + páginas: dashboard, supplies (+/new,
  +/[id] detalle con lotes), movements, production, categories, locations, reports,
  users (+/[id]/audit-log). Grupo protegido por `middleware.ts`.
- `src/app/api/reports/export/route.ts` — proxy autenticado que reenvía el CSV del backend.
- `src/components/` — SubmitButton, FormMessage, Sidebar, PageHeader, Icon (FontAwesome),
  AlertToaster (WebSocket), InfoBanner (explicación breve por módulo).
- Usuarios: componente `ResetPassword` (restablece la clave de un usuario, ver
  [[conceptos/recuperacion-contrasenas]]).

**Rutas:** login, dashboard, supplies, supplies/new, supplies/[id], movements, production,
categories, locations, reports, users, users/[id]/audit-log, **settings**, profile, más los
route handlers `api/reports/export`, `api/profile/avatar`, `api/settings/logo` y
`api/settings/login-background/[device]`.

**Iconografía:** [[conceptos/iconos-fontawesome-nextjs]] (FontAwesome SVG local, sin CDN).

## Añadido en 2026-07-09
- `components/MobileNav.tsx` — navegación por debajo de 768 px, que antes no existía;
  sidebar fijo con `h-screen sticky` ([[conceptos/navegacion-responsiva-y-sidebar-fijo]]).
- `components/Pagination.tsx` — paginación por enlaces
  ([[conceptos/paginacion-ui-searchparams]]).
- `components/ImageCropper.tsx` — recortador propio en canvas, sin dependencias nuevas
  ([[conceptos/recorte-imagenes-1a1-y-aspecto]]).
- `components/IconPicker.tsx` + `lib/categoryIcons.ts` — selector de iconos de categoría.
- `components/Footer.tsx` — copyright con año calculado y nombre configurado.
- `lib/format.ts` — `formatMoney`/`formatQuantity` reciben `{locale, currency}` explícito
  en vez de constantes; `labels.ts` los re-exporta.
- `lib/uploadProxy.ts` — proxy común de los tres uploads (el token vive en cookie httpOnly).
- `app/(dashboard)/settings/` — LogoForm, LoginBackgroundForm, BrandingForm, OperationForm,
  BusinessForm.
- Temas por variables CSS ([[conceptos/temas-css-variables-tailwind]]) y favicon derivado
  del logo, vía `generateMetadata`.

## Aparece en
- [[fuentes/sesion-frontend-nextjs-y-seed-admin]] — sesión de construcción inicial
- [[fuentes/sesion-frontend-modulos-avanzados]] — módulos avanzados (HU-08/10/11/12/13/14/15/16)
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — ajustes, responsive, paginación

## Relaciones
- [[entidades/pastrystock-manager]] — proyecto contenedor
- [[entidades/backend-pastrystock]] — API que consume
- Aplica [[conceptos/autenticacion-jwt-cookies-httponly]],
  [[conceptos/server-components-vs-server-actions]], [[conceptos/rbac]],
  [[conceptos/websockets-redis-pubsub]] (cliente WS) y
  [[conceptos/produccion-bom-transaccion-atomica]] (widget de dry-run)

## Notas
Build de producción usa `output: "standalone"` (requerido por el Dockerfile). En
Windows local el empaquetado falla por symlinks; usar `NEXT_DISABLE_STANDALONE=1`.
El stage `development` del Dockerfile se corrigió para instalar dependencias y así
preservarlas en el volumen anónimo `/app/node_modules`.

El hot-reload **no funciona** sin `WATCHPACK_POLLING=true` en el compose:
[[conceptos/hot-reload-docker-windows]].

**Deuda conocida:** `getSupply()` en `lib/queries.ts` resuelve un insumo por id pidiendo el
listado con `limit: 100` y filtrando en memoria — no existe `GET /supplies/{id}`. Dará 404
para los insumos más recientes al superar los 100.
