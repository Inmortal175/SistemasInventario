---
title: "RBAC (Control de acceso por rol)"
tags: [seguridad, autorizacion, rbac, reglas-negocio]
source_count: 1
---

# RBAC (Control de acceso por rol)

## Definición
Control de acceso basado en roles del sistema. Tres roles: **SUPERADMIN**, **ADMIN** y
**STAFF**. La autoridad se impone en el backend (dependencia `require_roles`) y se
**espeja** en el frontend para ocultar acciones no permitidas y evitar viajes inútiles.

## Fuentes que lo mencionan
- [[fuentes/sesion-frontend-nextjs-y-seed-admin]] — espejo del RBAC en el frontend
- [[fuentes/sesion-backend-completo-16-hu]] — imposición en backend (`require_roles`)

## Perspectivas/decisiones
- **STAFF** solo registra movimientos `EXIT` y `WASTE`; `ENTRY`, ajustes y `TRANSFER`
  son ADMIN+. En el frontend, el select de tipo de movimiento se filtra por rol
  (`MOVEMENTS_BY_ROLE` en `lib/labels.ts`).
- Alta de insumos / categorías / ubicaciones: solo ADMIN+. El frontend oculta los botones
  y, además, protege las páginas con `redirect` si un no-admin llega por URL.
- La autoridad real vive en el backend; el frontend es una capa de conveniencia/UX, no la
  frontera de seguridad.

- **SUPERADMIN** es exclusivo para la gestión de usuarios (HU-10): crear cuentas,
  suspender (con [[conceptos/blacklist-jwt-redis]]) y consultar el audit-log global.
- **ADMIN+** para conciliación (HU-11), reportes OLAP (HU-12) y gestión de lotes.
  **STAFF+** para consumo FIFO y producción BOM (HU-15).

## Contradicciones detectadas
Ninguna. Regla derivada de `ALLOWED_MOVEMENTS_BY_ROLE` en `backend/app/domain/enums.py`.
