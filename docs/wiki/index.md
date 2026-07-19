# Índice de la Wiki

Última actualización: 2026-07-19 | Total páginas: 54

## Fuentes (12)
| Página | Resumen | Fecha | Tags |
|--------|---------|-------|------|
| [[fuentes/sesion-frontend-nextjs-y-seed-admin]] | Construcción del frontend Next.js 15 y del seed de admin | 2026-07-08 | frontend, nextjs, autenticacion, seed |
| [[fuentes/sesion-backend-completo-16-hu]] | Completado del backend cubriendo las 16 historias de usuario | 2026-07-08 | backend, fastapi, fifo, produccion-bom, websockets |
| [[fuentes/sesion-frontend-modulos-avanzados]] | Frontend de módulos avanzados (HU-08/10/11/12/13/14/15/16) + FontAwesome | 2026-07-08 | frontend, nextjs, fontawesome, produccion, websockets |
| [[fuentes/sesion-recuperacion-y-ux-modulos]] | Recuperación de contraseñas (reset + época de sesión) y UX explicativa | 2026-07-08 | seguridad, contrasenas, jwt, ux |
| [[fuentes/sesion-perfil-y-cobertura-tests]] | Perfil de usuario, corrección de test de login y cobertura ≥80% | 2026-07-08 | usuarios, perfil, testing, cobertura |
| [[fuentes/sesion-avatar-pyjwt-y-test-db]] | Avatar de perfil, migración a PyJWT y aislamiento de la BD de tests | 2026-07-08 | avatar, pyjwt, testing, base-datos |
| [[fuentes/sesion-ajustes-branding-y-paginacion]] | Ajustes del sistema, branding, recorte de imágenes, responsive y paginación | 2026-07-09 | ajustes, branding, temas, uploads, paginacion, docker |
| [[fuentes/sesion-formalizacion-sdd-spec-kit]] | Evidencia formal de SDD (Spec Kit) en docs/spec/: constitución, análisis, plan, 71 tareas y trazabilidad | 2026-07-10 | sdd, spec-kit, metodologia, ciclo-de-vida, trazabilidad |
| [[fuentes/sesion-produccion-registro-y-producto-terminado]] | HU-17: producto terminado como inventario + registro inmutable de cada producción; suite 121 verde | 2026-07-10 | hu-17, produccion, producto-terminado, migracion, tests |
| [[fuentes/sesion-refinamientos-ux-auditoria-y-olap]] | Auto-crear producto desde receta + sección propia; auditoría legible en español; OLAP con costos y tipo | 2026-07-11 | hu-17, hu-12, hu-10, auditoria, ux, olap |
| [[fuentes/sesion-despliegue-railway-csrf-y-contrasenas]] | Puesta en producción en Railway tras 7 fallos encadenados; auditoría CSRF; ojito en contraseñas | 2026-07-17 | despliegue, railway, alembic, docker, seguridad, csrf, ux, cve |
| [[fuentes/sesion-reset-sistema-y-cache-first-seed]] | Reset del sistema + seed que invalida caché; el 502 de Railway era Target Port, no código | 2026-07-19 | railway, redis, cache-first, seed, reset, operaciones |

## Entidades (6)
| Página | Tipo | Aparece en |
|--------|------|-----------|
| [[entidades/pastrystock-manager]] | proyecto | sesion-frontend-nextjs-y-seed-admin, sesion-backend-completo-16-hu, sesion-ajustes-branding-y-paginacion |
| [[entidades/backend-pastrystock]] | modulo | sesion-backend-completo-16-hu, sesion-ajustes-branding-y-paginacion |
| [[entidades/frontend-nextjs]] | modulo | sesion-frontend-nextjs-y-seed-admin, sesion-ajustes-branding-y-paginacion |
| [[entidades/script-seed-admin]] | herramienta | sesion-frontend-nextjs-y-seed-admin |
| [[entidades/script-seed-demo]] | herramienta | sesion-ajustes-branding-y-paginacion, sesion-reset-sistema-y-cache-first-seed |
| [[entidades/script-reset-system]] | herramienta | sesion-reset-sistema-y-cache-first-seed |

## Conceptos (36)
| Página | Resumen breve | Fuentes |
|--------|--------------|---------|
| [[conceptos/producto-terminado-y-registro-de-produccion]] | Producto terminado como inventario + corridas inmutables (HU-17) | 1 |
| [[conceptos/spec-driven-development-spec-kit]] | SDD y estructura de artefactos Spec Kit; trazabilidad como evidencia | 1 |
| [[conceptos/autenticacion-jwt-cookies-httponly]] | JWT en cookies httpOnly, no en localStorage | 1 |
| [[conceptos/iconos-fontawesome-nextjs]] | Iconografía FontAwesome SVG local + selector con lista blanca | 2 |
| [[conceptos/recuperacion-contrasenas]] | Reset por admin/CLI + época de sesión (iat) | 1 |
| [[conceptos/gestion-perfil-usuario]] | Perfil self-service: editar nombre y cambiar clave | 1 |
| [[conceptos/avatar-perfil-y-estaticos]] | Foto de perfil: upload, estáticos, cookie de sesión y recorte 1:1 | 2 |
| [[conceptos/aislamiento-bd-tests]] | Tests de integración contra pastry_test desechable | 1 |
| [[conceptos/server-components-vs-server-actions]] | Lectura server-side, mutación por actions | 1 |
| [[conceptos/rbac]] | Roles SUPERADMIN/ADMIN/STAFF, impuestos en backend y espejados en frontend | 2 |
| [[conceptos/seed-idempotente]] | Bootstrap sin duplicados, reejecutable | 2 |
| [[conceptos/fifo-lotes-vencimiento]] | Consumo de lotes por fecha de vencimiento (FIFO) | 1 |
| [[conceptos/produccion-bom-transaccion-atomica]] | Recetas BOM: descuento atómico, rollback, lista de preparación y snapshot histórico | 1 |
| [[conceptos/valorizacion-inventario]] | Valor de activos y pérdida por mermas | 1 |
| [[conceptos/rate-limiting-redis]] | Bloqueo de login por IP con Redis | 1 |
| [[conceptos/blacklist-jwt-redis]] | Invalidación de sesión en JWT stateless | 1 |
| [[conceptos/websockets-redis-pubsub]] | Alertas en tiempo real vía WS + Pub/Sub | 1 |
| [[conceptos/olap-export-desnormalizado]] | Exportación CSV plana para ETL/OLAP | 1 |
| [[conceptos/cache-first-paginacion]] | Listados paginados cache-first con Redis | 2 |
| [[conceptos/configuracion-sistema-en-bd]] | system_settings singleton; frontera negocio vs. despliegue | 1 |
| [[conceptos/temas-css-variables-tailwind]] | Paletas en runtime con variables CSS y `<alpha-value>` | 1 |
| [[conceptos/recorte-imagenes-1a1-y-aspecto]] | Canvas en el cliente, Pillow en el servidor | 1 |
| [[conceptos/fondo-login-responsivo]] | Tres fondos por dispositivo, `<picture>` y cadena de respaldo | 1 |
| [[conceptos/paginacion-ui-searchparams]] | Paginación por enlaces `?page=N` en Server Components | 1 |
| [[conceptos/navegacion-responsiva-y-sidebar-fijo]] | Drawer móvil y `h-screen sticky` en el aside | 1 |
| [[conceptos/hot-reload-docker-windows]] | inotify no funciona en bind-mounts: `WATCHPACK_POLLING` | 1 |
| [[conceptos/cache-obsoleta-tras-cambio-de-schema]] | Una entrada de Redis vieja puede devolver 500 tras migrar | 1 |
| [[conceptos/cobertura-y-greenlet-sqlalchemy]] | coverage.py deja de trazar tras el primer await a la BD | 1 |
| [[conceptos/despliegue-en-paas-vs-docker-compose]] | Lo que compose hacía por ti y en un PaaS no hace nadie | 1 |
| [[conceptos/enums-postgres-alembic-vs-init-sql]] | El esquema entero debe vivir en Alembic, no en init.sql | 1 |
| [[conceptos/arranque-de-contenedor-y-healthcheck]] | Las migraciones no deben poder bloquear el arranque | 1 |
| [[conceptos/proteccion-csrf-bearer-vs-cookies]] | La superficie CSRF está donde vive la cookie | 1 |
| [[conceptos/reproducir-el-contenedor-de-produccion-en-local]] | Depurar el despliegue en segundos, no en ciclos de 5 min | 1 |
| [[conceptos/campo-contrasena-con-visibilidad]] | El "ojito": un componente, seis campos, accesible | 1 |
| [[conceptos/invalidacion-cache-al-sembrar-directo-a-db]] | Escribir directo a la DB obliga a invalidar las llaves cache-first | 1 |
| [[conceptos/railway-target-port-vs-port-escucha]] | 502 Bad Gateway: el Target Port debe coincidir con el puerto de escucha | 1 |

## Síntesis (0)
| Página | Origen | Fecha |
|--------|--------|-------|
