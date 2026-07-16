# Matriz de Trazabilidad

> **Artefacto SDD:** cierre de la cadena de evidencia. Demuestra que **cada requisito recorre
> todo el ciclo**: Requisito → Historia → Tarea → Código → Prueba → Estado. Es la respuesta
> directa a "¿esto es SDD real o solo una app generada?": si la cadena está cerrada para las 16
> HU, el desarrollo estuvo gobernado por la especificación.

Sentido de lectura: **de izquierda (qué se pidió) a derecha (dónde se implementó y cómo se verifica).**

---

## 1. Matriz principal: HU → Tarea → Código → Prueba

| HU | RF | Tareas | Endpoint | Servicio | Prueba(s) | Estado |
|---|---|---|---|---|---|---|
| HU-01 | RF-01 | T-CAT-01/02/03 | `endpoints/categories.py` | `category_service.py` | `test_category_service.py` · TC-CAT-01/02 | ✅ |
| HU-02 | RF-02 | T-SUP-03/04/05, T-ALR-01 | `endpoints/movements.py` | `supply_service.py`, `alert_service.py` | `test_supply_service.py` · TC-MOV-01, TC-SVC-01 | ✅ |
| HU-03 | RF-03 | T-DOM-01, T-LOC-01/02 | `endpoints/locations.py` | `location_service.py` | `test_location_service.py`, `test_domain_value_objects.py` | ✅ |
| HU-04 | RF-04 | T-AUTH-01/02/03 | `endpoints/auth.py` | `auth_service.py`, `core/security.py` | `test_auth_rate_limit.py` | ✅ |
| HU-05 | RF-05 | T-SUP-01 | `endpoints/supplies.py` | `supply_service.py` | `test_supply_service.py` | ✅ |
| HU-06 | RF-06 | T-SUP-02 | `endpoints/supplies.py` | `supply_service.py` (cache) | `test_advanced_api.py` | ✅ |
| HU-07 | RF-07 | T-SUP-05/07 | `endpoints/supplies.py` | `supply_service.py` | `test_supply_movements_history.py` | ✅ |
| HU-08 | RF-08 | T-DSH-01 | `endpoints/dashboard.py` | `dashboard_service.py` | `test_advanced_api.py` | ✅ |
| HU-09 | RF-09 | T-SUP-06 | `endpoints/movements.py` | `supply_service.py` | `test_supply_service.py` | ✅ |
| HU-10 | RF-10 | T-USR-01/02/03 | `endpoints/users.py` | `user_service.py` | `test_advanced_api.py` | ✅ |
| HU-11 | RF-11 | T-SUP-08 | `endpoints/supplies.py` | `supply_service.py` | `test_reconciliation_service.py` | ✅ |
| HU-12 | RF-12 | T-RPT-01/02 | `endpoints/reports.py` | `report_service.py` | `test_report_service.py` | ✅ |
| HU-13 | RF-13 | T-BAT-01/02/03 | `endpoints/batches.py` | `batch_service.py` | `test_batch_fifo_service.py` | ✅ |
| HU-14 | RF-14 | T-WS-01/02, T-ALR-01 | `endpoints/websocket.py` | `pubsub_listener.py`, `alert_service.py` | `test_advanced_api.py` | ✅ |
| HU-15 | RF-15 | T-PRD-01/02 | `endpoints/production.py` | `production_service.py` | `test_production_service.py` | ✅ |
| HU-16 | RF-16 | T-BAT-04, T-DSH-02 | `endpoints/batches.py`, `endpoints/dashboard.py` | `batch_service.py`, `dashboard_service.py` | `test_advanced_api.py` | ✅ |
| HU-17 | RF-17 | T-FIN-01…09 | `endpoints/production.py` | `production_service.py`, `production_run_repository.py` | `test_production_service.py` (`...registers_finished_product_and_run`) | ✅ |

## 2. Cobertura de escenarios (SC) por caso de prueba

| Escenario | Verificado por |
|---|---|
| SC-HU01-01 (creación + Redis) | TC-CAT-01 |
| SC-HU01-02 (duplicado cache-first) | TC-CAT-02 |
| SC-HU01-03 (403 a STAFF) | `test_advanced_api.py` (RBAC) |
| SC-HU02-01/02 (consumo + alerta) | TC-MOV-01 |
| SC-HU02-03 (stock insuficiente) | TC-SVC-01 |
| SC-HU03-01/02 (código válido/ inválido) | TC-DOMAIN-01/02/03 |
| SC-HU04-02 (rate limit) | `test_auth_rate_limit.py` |
| SC-HU07-01 (historial) | TC-HIST-01…03 |
| SC-HU11-01/03 (ajuste + alerta) | `test_reconciliation_service.py` |
| SC-HU12-01 (export OLAP) | `test_report_service.py` |
| SC-HU13-02 (FIFO) | `test_batch_fifo_service.py` |
| SC-HU15-01/02 (BOM + rollback) | `test_production_service.py` |

## 3. Trazabilidad de reglas de negocio (Constitución Art. IV)

| Regla | Defensa en dominio/servicio | Defensa en BD | Prueba |
|---|---|---|---|
| Patrón `LocationCode` | `value_objects.LocationCode` | `CHECK (code ~ ...)` | `test_domain_value_objects.py` |
| `movement_history` inmutable | Sin update en servicio | Sin `updated_at`, FK `RESTRICT` | `test_supply_movements_history.py` |
| Stock nunca negativo | `SupplyService` valida | `CHECK current_stock >= 0` | `test_supply_service.py` |
| STAFF solo EXIT/WASTE | `ALLOWED_MOVEMENTS_BY_ROLE` | RBAC en router | `test_domain_value_objects.py` |
| Cache-first categorías | `category_service` (Redis→PG) | — | `test_category_service.py` |

## 4. Trazabilidad de fases del ciclo de vida

| Fase | Entrada | Salida (artefacto) | Bloque de tareas |
|---|---|---|---|
| Análisis | Problema del negocio | `01-analisis.md`, `user-stories.md` | Bloque 1 |
| Diseño | RF/RNF | `03-plan.md`, `architecture.md`, `database-schema.md` | Bloques 0, 2 |
| Implementación | Diseño | Código en `backend/app/`, `frontend/src/` | Bloques 3–9 |
| Pruebas | HU + código | `test-matrix.md`, `backend/tests/` | Bloque 10 |
| Despliegue | Sistema probado | `05-deployment.md`, `docker-compose*.yml` | Bloque 11 |

## 5. Estado global

- **HU con cadena cerrada (Requisito→…→Prueba):** 16 / 16.
- **Bloques de tareas completados:** 11 / 12 (pendiente solo T-DOC-03, informe final).
- **Conclusión:** la especificación gobernó el desarrollo end-to-end; el proyecto evidencia SDD,
  no generación de código sin control.

> Mantenimiento: al cambiar cualquier comportamiento, esta matriz debe volver a cerrarse (spec →
> tarea → código → prueba) antes de dar la tarea por hecha (Constitución, Art. I).
