# Fase 2 — Especificación (Spec)

> **Artefacto SDD:** núcleo del método. Enumera *qué* debe hacer el sistema mediante Historias
> de Usuario con criterios de aceptación verificables. El detalle completo en formato BDD/Gherkin
> vive en [`../user-stories.md`](../user-stories.md); este documento es el **índice maestro** que
> da a cada HU un identificador estable, su rol, su prioridad y su enlace de trazabilidad.

- **Total de Historias de Usuario:** 17
- **Total de escenarios de aceptación (SC):** 39
- **Fuente canónica de escenarios:** `docs/user-stories.md`
- **Trazabilidad a código y pruebas:** `06-traceability.md`

---

## Glosario de roles (RBAC)

| Rol | Capacidades |
|---|---|
| **SUPERADMIN** | Cuentas de usuario, auditoría global, parametrización del sistema |
| **ADMIN** | Categorías, insumos, ubicaciones, `ENTRY`, `ADJUSTMENT`, reportes |
| **STAFF** | Solo `EXIT` y `WASTE`; producción de recetas; sin reportes globales |

## Convención de identificadores

- **HU-NN** — Historia de Usuario.
- **SC-HUNN-MM** — Escenario de aceptación (Given/When/Then) de la HU.
- **RF-NN** — Requisito funcional de origen (ver `01-analisis.md`).

---

## Índice maestro de Historias de Usuario

| HU | Título | Rol principal | Prioridad | Escenarios | Módulo backend |
|---|---|---|---|---|---|
| HU-01 | Creación dinámica de categorías | ADMIN+ | Crítica | 5 | `categories` / `category_service` |
| HU-02 | Registro de consumo de insumos | STAFF | Crítica | 3 | `movements` / `supply_service` + `alert_service` |
| HU-03 | Gestión de ubicaciones físicas | ADMIN+ | Alta | 2 | `locations` / `location_service` |
| HU-04 | Login y emisión de JWT | Todos | Crítica | 2 | `auth` / `auth_service` + `core/security` |
| HU-05 | Gestión de ítems de insumo (CRUD) | ADMIN | Crítica | 1 | `supplies` / `supply_service` |
| HU-06 | Listado con filtros y paginación | Todos | Alta | 2 | `supplies` / `supply_service` (cache) |
| HU-07 | Historial de movimientos (auditoría) | ADMIN+ | Alta | 1 | `supplies` / `supply_service` |
| HU-08 | Dashboard de KPIs en tiempo real | ADMIN+ | Media | 1 | `dashboard` / `dashboard_service` |
| HU-09 | Reabastecimiento (ENTRY) | ADMIN | Alta | 1 | `movements`/`batches` / `supply_service` |
| HU-10 | Gestión de usuarios y trazabilidad | SUPERADMIN | Crítica | 3 | `users` / `user_service` + blacklist Redis |
| HU-11 | Conciliación y ajustes | ADMIN+ | Alta | 3 | `supplies` / `supply_service` |
| HU-12 | Exportación OLAP-ready | ADMIN+ | Media | 2 | `reports` / `report_service` |
| HU-13 | Control de lotes y FIFO | ADMIN/STAFF | Crítica | 3 | `batches` / `batch_service` |
| HU-14 | Alertas en tiempo real (WebSocket) | ADMIN+ | Media | 2 | `websocket` / `pubsub_listener` + `alert_service` |
| HU-15 | Producción por recetas (BOM) | STAFF/ADMIN | Crítica | 2 | `production` / `production_service` |
| HU-16 | Proveedores y valorización financiera | ADMIN+ | Media | 2 | `batches`/`dashboard` / `batch_service` + `dashboard_service` |
| HU-17 | Registro de producción y stock de producto terminado | ADMIN/STAFF | Crítica | 4 | `production` / `production_service` + `batch_service` |

## Criterios de aceptación transversales (aplican a toda HU)

1. **Autorización:** toda ruta protegida rechaza con `403` a roles no autorizados y con `401`
   a peticiones sin token válido.
2. **Validación:** payloads inválidos devuelven `422` con detalle del campo que falló.
3. **Errores de negocio:** se devuelven con un `error_code` estable (p. ej.
   `INSUFFICIENT_STOCK`, `CATEGORY_NAME_ALREADY_EXISTS`, `INSUFFICIENT_PERMISSIONS`).
4. **Auditoría:** toda mutación de stock deja un registro inmutable en `movement_history` con
   `user_id`, `stock_before`, `stock_after` y `timestamp`.
5. **Consistencia:** las mutaciones que afectan catálogo/listados invalidan la caché Redis.

## Ejemplo de escenario (referencia de formato)

Extraído de HU-02 (`SC-HU02-03 — Rechazo por stock insuficiente`):

```gherkin
Dado que el insumo tiene current_stock=3.000
Cuando STAFF intenta EXIT de 5.000 KG
Entonces el sistema calcula 3.000 - 5.000 = -2.000 (INVÁLIDO por ser < 0)
  Y retorna HTTP 422 con error_code="INSUFFICIENT_STOCK"
  Y el body contiene { available_stock: 3.000, requested: 5.000 }
  Y NO modifica current_stock en PostgreSQL
  Y NO inserta en movement_history
```

> El conjunto completo de los 35 escenarios está en `docs/user-stories.md`. Cada uno se
> convierte en una o más tareas (`04-tasks.md`) y en uno o más casos de prueba (`test-matrix.md`).
