# Matriz de Casos de Prueba

Metodología: **Spec-Driven Testing (SDT)**
Framework: `pytest` + `pytest-asyncio` + `httpx`

---

## Resumen

| ID | Tipo | Módulo | Prioridad | HU Cubierta | Estado |
|---|---|---|---|---|---|
| TC-DOMAIN-01 a 08 | Unitario | domain/ | CRÍTICA | HU-01, HU-02 | Implementado |
| TC-CAT-01 | Integración | categories | CRÍTICA | HU-01 SC-01 | Pendiente |
| TC-CAT-02 | Integración | categories | CRÍTICA | HU-01 SC-02 | Pendiente |
| TC-MOV-01 | Integración | movements | CRÍTICA | HU-02 SC-01+02 | Pendiente |
| TC-SVC-01 | Unitario | SupplyService | CRÍTICA | HU-02 SC-03 | Pendiente |
| TC-HIST-01 a 03 | Unitario | SupplyService | ALTA | HU-07 SC-01 | Implementado |
| TC-PROD-01 | Unitario | ProductionService | CRÍTICA | HU-17 SC-01 (`test_production_service.py::...registers_finished_product_and_run`) | Implementado |
| TC-PROD-02 | Integración | production/supplies | CRÍTICA | HU-17 SC-01+02+03 (`test_advanced_api.py::...finished_product_stock_and_history`) | Implementado |
| TC-RPT-OLAP | Unitario | ReportService | ALTA | HU-12 (columnas OLAP + item_type/costos) | Implementado |
| TC-AUDIT-01 | Integración | users/audit-log | MEDIA | HU-10 SC-03 (resumen legible) | Implementado |

---

## TC-DOMAIN-01 a TC-DOMAIN-08 — Dominio Puro

**Archivo:** `tests/unit/test_domain_value_objects.py`
**Dependencias externas:** ninguna (stdlib Python únicamente)

| Sub-TC | Descripción | Resultado esperado |
|---|---|---|
| 01 | LocationCode códigos válidos (8 casos) | Sin excepción |
| 02 | LocationCode normaliza a mayúsculas | `est-01` → `EST-01` |
| 03 | LocationCode códigos inválidos (8 casos) | `LocationCodeInvalidError` |
| 04 | InsufficientStockError lleva contexto | `.available`, `.requested`, `.error_code` |
| 05 | STAFF solo puede EXIT y WASTE | Conjunto correcto |
| 06 | ADMIN puede todos los MovementType | `set == set(MovementType)` |
| 07 | SUPERADMIN puede todos los MovementType | `set == set(MovementType)` |
| 08 | LocationCode.location_type derivado de prefijo | EST→SHELF, REF→REFRIGERATOR |

---

## TC-CAT-01 — Creación de categoría: persistencia dual PostgreSQL + Redis

**Archivo:** `tests/integration/test_category_endpoints.py`
**Tipo:** Integración con BD de test + Redis mock

```
PRECONDICIÓN: BD limpia, categoría inexistente
ACCIÓN:       POST /api/v1/categories con token ADMIN
VERIFICAR:    1. HTTP 201
              2. Respuesta contiene UUID y slug generado
              3. Registro existe en PostgreSQL (query directo)
              4. redis.set() llamado con clave "category:{id}" y ex=3600
```

---

## TC-CAT-02 — Duplicado detectado cache-first (sin tocar PostgreSQL)

**Archivo:** `tests/integration/test_category_endpoints.py`

```
PRECONDICIÓN: Categoría "Harinas Especiales" en Redis mock (simula cache caliente)
ACCIÓN:       POST /api/v1/categories con name="Harinas Especiales"
VERIFICAR:    1. HTTP 409
              2. error_code="CATEGORY_NAME_ALREADY_EXISTS"
              3. redis.get() fue llamado (cache consultado)
              4. CategoryRepository.get_by_name() NO fue llamado (PostgreSQL no tocado)
```

---

## TC-MOV-01 — Consumo con stock crítico: alerta Redis publicada

**Archivo:** `tests/integration/test_movement_endpoints.py`

```
PRECONDICIÓN: Insumo con current_stock=12.000, minimum_stock=10.000
ACCIÓN:       POST /api/v1/movements { type: EXIT, quantity: 5.0 } con token STAFF
VERIFICAR:    1. HTTP 201
              2. response.stock_after == 7.0
              3. response.alert_triggered == true
              4. Header X-Alert-Triggered: true
              5. redis.publish() llamado en channel "alerts:low_stock"
              6. Payload del evento contiene deficit=3.0
              7. movement_history tiene 1 registro en BD con alert_triggered=true
```

---

## TC-SVC-01 — Stock insuficiente: excepción de dominio sin escritura en BD

**Archivo:** `tests/unit/test_supply_service.py`
**Tipo:** Unitario puro (repositorios mockeados)

```
PRECONDICIÓN: SupplyService instanciado con repos mock; insumo retorna stock=3.000
ACCIÓN:       supply_service.register_consumption(quantity=5.000)
VERIFICAR:    1. Lanza InsufficientStockError
              2. exc.available == Decimal("3.000")
              3. exc.requested == Decimal("5.000")
              4. movement_repository.create() → NOT called
              5. supply_repository.update_stock() → NOT called
```

---

## Configuración de pytest

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --cov=app --cov-report=term-missing --cov-fail-under=80"
```

## Fixtures globales (conftest.py)

| Fixture | Scope | Descripción |
|---|---|---|
| `async_client` | function | `httpx.AsyncClient` apuntando a la app FastAPI |
| `db_session` | function | `AsyncSession` con rollback automático post-test |
| `admin_auth_headers` | function | Headers JWT con rol ADMIN |
| `staff_auth_headers` | function | Headers JWT con rol STAFF |
| `mock_redis_client` | function | `AsyncMock` de Redis |
| `supply_item_near_minimum` | function | Insumo con stock=12, mínimo=10 |
| `existing_category` | function | Categoría activa en BD y en mock Redis |
