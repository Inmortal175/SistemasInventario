---
title: "Sesión: Frontend — módulos avanzados y FontAwesome"
date: 2026-07-08
source_url: ""
source_path: ""
type: sesion-desarrollo
tags: [frontend, nextjs, fontawesome, produccion, websockets, rbac, reportes]
---

# Sesión: Frontend — módulos avanzados y FontAwesome

## Resumen
Extensión del frontend Next.js 15 para cubrir los módulos del backend que quedaban sin UI:
dashboard con KPIs/valorización reales (HU-08/16), producción con simulacro (HU-15),
lotes FIFO + conciliación en el detalle de insumo (HU-11/13/16), gestión de usuarios y
auditoría (HU-10), exportación CSV (HU-12) y alertas en tiempo real por WebSocket (HU-14).
Se migró la iconografía de emojis a FontAwesome (SVG local). El frontend pasó de 11 a 15
rutas. Verificado: `tsc --noEmit` limpio, `next build` OK (15/15 páginas), y render real
en el navegador contra el stack Docker.

## Ideas clave
- **Iconos**: [[conceptos/iconos-fontawesome-nextjs]] — registro central `Icon.tsx`,
  `autoAddCss=false` para no romper SSR.
- **Producción con dry-run**: el `ProduceWidget` (cliente) llama a `/production/simulate`
  y muestra una tabla de viabilidad (requerido/disponible/déficit); el botón "Producir"
  solo se habilita si `feasible=true`. Refleja [[conceptos/produccion-bom-transaccion-atomica]].
- **Detalle de insumo** (`/supplies/[id]`): lotes en orden FIFO, alta de lote (ADMIN+),
  consumo FIFO y conciliación, más el historial de movimientos.
- **RBAC en la UI**: el sidebar filtra entradas por rol y las páginas sensibles hacen
  `redirect` si el rol no corresponde (Reportes/Usuarios). Espeja [[conceptos/rbac]].
- **CSV**: route handler `/api/reports/export` que adjunta el bearer (token en cookie
  httpOnly) y reenvía el archivo como descarga. Ver [[conceptos/olap-export-desnormalizado]].
- **Alertas en vivo**: `AlertToaster` (cliente) abre el WebSocket con el token pasado
  desde el layout (server component) y muestra toasts de stock/vencimiento.
  Ver [[conceptos/websockets-redis-pubsub]].

## Verificación realizada
- `tsc --noEmit` sin errores; `next build` OK (15 rutas).
- Render con sesión real: dashboard (KPIs + valor activo + mermas), producción
  (simular/producir/recetas), usuarios (tabla + suspender + auditoría), detalle de insumo
  (lotes/FIFO/conciliación), descarga CSV con cabeceras correctas.
- Guards de rol: STAFF recibe 307 en `/users` y `/reports`, y su sidebar no los lista.

## Entidades mencionadas
- [[entidades/frontend-nextjs]] — módulo ampliado en esta sesión
- [[entidades/backend-pastrystock]] — API consumida

## Conceptos relacionados
- [[conceptos/iconos-fontawesome-nextjs]]
- [[conceptos/server-components-vs-server-actions]]
- [[conceptos/rbac]]
- [[conceptos/websockets-redis-pubsub]]
- [[conceptos/produccion-bom-transaccion-atomica]]
- [[conceptos/olap-export-desnormalizado]]

## Notas de síntesis
Durante la verificación se detectó que la BD había sido truncada por una corrida de la
suite de integración (`pytest tests/integration`) contra la base real (quedó un usuario
de fixture `admin-*@test.local` y 0 insumos/lotes/recetas). No afectó el código del
frontend; se re-sembró el superadmin con `scripts/seed_admin.py`. **Lección**: las pruebas
de integración deben apuntar a una BD desechable, no a la de desarrollo con datos vivos.
