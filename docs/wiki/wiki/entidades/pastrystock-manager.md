---
title: "PastryStock Manager"
type: proyecto
tags: [inventario, pasteleria, fastapi, nextjs, mvp]
---

# PastryStock Manager

## Descripción
MVP de sistema de gestión de inventario para pastelerías. Maneja insumos perecederos,
herramientas de cocina y útiles de limpieza con control RBAC, categorización dinámica
con caché Redis, ubicaciones físicas rotuladas y auditoría inmutable de movimientos.

**Stack:** FastAPI + SQLAlchemy 2.0 async + asyncpg · Next.js 15 App Router + TypeScript
+ Tailwind · PostgreSQL 16 · Redis 7 · Docker Compose.

**Metodología:** SDD (historias BDD/Gherkin en `docs/user-stories.md`), TDD, SOLID con
arquitectura limpia por capas (domain / infrastructure / application / api / core).

## Aparece en
- [[fuentes/sesion-frontend-nextjs-y-seed-admin]] — construcción del frontend y seed
- [[fuentes/sesion-backend-completo-16-hu]] — completado del backend (16 HUs)
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — configurabilidad, branding y paginación
- [[fuentes/sesion-formalizacion-sdd-spec-kit]] — evidencia formal de SDD en `docs/spec/`
- [[fuentes/sesion-produccion-registro-y-producto-terminado]] — HU-17: producto terminado + registro de producción

## Relaciones
- [[entidades/backend-pastrystock]] — capa de API y lógica de negocio
- [[entidades/frontend-nextjs]] — capa de presentación
- [[entidades/script-seed-admin]] — utilidad de bootstrap del primer usuario
- [[entidades/script-seed-demo]] — escenario de simulación (Torta de Chocolate)

## Configurabilidad
Desde 2026-07-09 la instalación es personalizable en caliente desde `/settings` (solo
SUPERADMIN): nombre, logo, paleta de color, fondos del login por dispositivo, moneda,
formato regional, tamaño de página, umbral de alerta de vencimiento e identidad fiscal.
Todo vive en la tabla `system_settings` — ver [[conceptos/configuracion-sistema-en-bd]].

## Notas
Reglas de negocio críticas: `LocationCode` con patrón `^(EST|REF|FRZ|CAB|CON|ALM)-\d{2}(-F\d{1,2})?$`
(solo EST admite sufijo de fila); `movement_history` inmutable; stock nunca negativo;
STAFF solo registra EXIT/WASTE; creación de categorías cache-first (Redis → PostgreSQL).

**Entorno de desarrollo (Windows + Docker):** el hot-reload del frontend requiere
`WATCHPACK_POLLING=true` en el compose — ver [[conceptos/hot-reload-docker-windows]].
