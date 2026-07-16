# Esquema de Base de Datos

## Tablas y Relaciones

### `users`
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID (PK) | `default uuid4` |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX |
| full_name | VARCHAR(255) | NOT NULL |
| hashed_password | VARCHAR(255) | NOT NULL |
| role | ENUM(user_role) | NOT NULL, INDEX |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | server_default now() |
| updated_at | TIMESTAMPTZ | server_default now(), onupdate |

### `locations`
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID (PK) | |
| code | VARCHAR(20) | UNIQUE, CHECK pattern |
| description | VARCHAR(255) | nullable |
| location_type | ENUM(location_type) | NOT NULL |
| capacity_units | INTEGER | nullable |
| is_active | BOOLEAN | DEFAULT true |

**Constraint crítico:**
```sql
CHECK (code ~ '^(EST|REF|FRZ|CAB|CON|ALM)-\d{2}(-F\d{1,2})?$')
```

Ejemplos válidos: `EST-01`, `EST-01-F2`, `REF-02`, `FRZ-01`, `CAB-03`, `CON-01`, `ALM-99`

Solo el prefijo `EST` (estante) admite sufijo de fila `-FX`.

### `dynamic_categories`
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID (PK) | |
| name | VARCHAR(100) | UNIQUE, NOT NULL |
| slug | VARCHAR(120) | UNIQUE, NOT NULL, INDEX |
| description | VARCHAR(500) | nullable |
| color_hex | VARCHAR(7) | NOT NULL (Ej: #FF6B9D) |
| icon_name | VARCHAR(50) | nullable |
| is_active | BOOLEAN | DEFAULT true, INDEX |
| created_by | UUID (FK→users) | ondelete=RESTRICT |

### `supply_items`
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID (PK) | |
| name | VARCHAR(255) | NOT NULL, INDEX |
| sku | VARCHAR(100) | UNIQUE, NOT NULL |
| category_id | UUID (FK→dynamic_categories) | INDEX |
| location_id | UUID (FK→locations) | |
| unit_of_measure | ENUM(unit_measure) | NOT NULL |
| current_stock | NUMERIC(10,3) | CHECK ≥ 0 |
| minimum_stock | NUMERIC(10,3) | |
| maximum_stock | NUMERIC(10,3) | CHECK min ≤ max |
| unit_cost | NUMERIC(12,4) | CHECK ≥ 0 |
| is_perishable | BOOLEAN | DEFAULT false |
| expiration_date | DATE | nullable |
| supplier_name | VARCHAR(255) | nullable |
| is_active | BOOLEAN | DEFAULT true |
| created_by | UUID (FK→users) | |

### `movement_history` ⚠️ INMUTABLE
| Columna | Tipo | Restricción |
|---|---|---|
| id | UUID (PK) | |
| supply_item_id | UUID (FK→supply_items) | INDEX |
| movement_type | ENUM(movement_type) | NOT NULL |
| quantity | NUMERIC(10,3) | NOT NULL |
| stock_before | NUMERIC(10,3) | NOT NULL |
| stock_after | NUMERIC(10,3) | NOT NULL |
| notes | VARCHAR(500) | nullable |
| alert_triggered | BOOLEAN | DEFAULT false |
| performed_by | UUID (FK→users) | INDEX |
| created_at | TIMESTAMPTZ | server_default now() |

**Sin `updated_at`** — garantía de inmutabilidad. Una vez insertado, ningún UPDATE es posible por diseño de la aplicación.

## ENUMs de Dominio

Definidos en `backend/sql/init.sql` con `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object`:

| Nombre | Valores |
|---|---|
| `user_role` | SUPERADMIN, ADMIN, STAFF |
| `unit_measure` | KG, GR, L, ML, UNIT, PKG, BOX, DOZEN |
| `movement_type` | ENTRY, EXIT, ADJUSTMENT_ADD, ADJUSTMENT_SUB, WASTE, TRANSFER |
| `location_type` | SHELF, REFRIGERATOR, FREEZER, CABINET, COUNTER, WAREHOUSE |

## Índices de Rendimiento

```sql
-- Búsqueda frecuente por categoría + estado
CREATE INDEX ix_supply_category_active ON supply_items(category_id, is_active);

-- Auditoría: historial por insumo ordenado por fecha DESC
CREATE INDEX ix_movement_item_date ON movement_history(supply_item_id, created_at);

-- Categorías activas (consulta de alta frecuencia desde Redis miss)
CREATE INDEX ix_categories_slug_active ON dynamic_categories(slug, is_active);
```

## Decisiones de Diseño

1. **UUID v4 como PK** en todas las tablas: evita enumeración, facilita sharding futuro.
2. **`ondelete=RESTRICT` en FKs**: protege la integridad; nunca borrado en cascada en inventario.
3. **`Numeric(10,3)` para stock**: permite hasta 9,999,999.999 unidades con 3 decimales (precisión para gramos y mililitros).
4. **`server_default=func.now()`**: los timestamps los pone PostgreSQL, no el cliente; elimina problemas de zona horaria del servidor de aplicación.
