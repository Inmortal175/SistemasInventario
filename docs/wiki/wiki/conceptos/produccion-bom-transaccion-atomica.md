---
title: "Producción BOM con transacción atómica"
tags: [produccion, bom, recetas, transaccion, rollback]
source_count: 1
---

# Producción BOM con transacción atómica

## Definición
Registro de producción de un producto final (ej. "Torta Tres Leches") que descuenta
automáticamente los insumos según una receta (Bill of Materials). La operación es
atómica: o se descuentan TODOS los ingredientes, o ninguno.

## Implementación (HU-15)
- Modelos `recipes` y `recipe_items` (ingrediente + `quantity_per_unit`).
- **Dry-run / Simulacro de stock**: `POST /api/v1/production/simulate` (solo lectura,
  sin locks ni escritura) responde `{feasible, ingredients[], missing[]}` con el déficit
  de cada faltante. Permite al maestro pastelero preguntar "¿me alcanza para N?" antes de
  comprometer la producción. Usa la misma aritmética que `produce`.
- **Lista de preparación (picking list)** (2026-07-15): cada `SimulatedIngredient` incluye
  ahora `unit`, `location_code`/`location_type` (dónde encontrarlo físicamente) y
  `batch_plan[]` — previsualización FIFO de qué lotes extraer y cuánto de cada uno
  (`batch_code`, `expiration_date`, `take`), sin descontar. Resuelve el problema de tener
  que ubicar a mano cada insumo y su proporción antes de producir. La ubicación vive en el
  `supply_item` (los lotes no tienen ubicación propia); el plan lo arma
  `BatchRepository.list_active_fifo` (solo lectura, sin `FOR UPDATE`). Se muestra en el
  `ProduceWidget` del frontend bajo cada ingrediente.
- `ProductionService.produce` en dos fases dentro de un lock:
  1. **Validación total**: por cada ingrediente calcula `need = quantity_per_unit × qty`
     y verifica `current_stock ≥ need`. Si uno falla, lanza
     `RecipeProductionShortageError` (error_code `RECIPE_PRODUCTION_FAILED_STOCK_SHORTAGE`,
     HTTP 422) con `{supply_id, required, available}`.
  2. **Descuento**: consume FIFO cada ingrediente (reutiliza
     [[conceptos/fifo-lotes-vencimiento]]) o el stock directo si el insumo no usa lotes,
     y registra un movimiento EXIT por ingrediente.
- El ROLLBACK lo garantiza el dependency de sesión (`get_async_session` hace rollback
  ante cualquier excepción). La validación previa asegura que ni siquiera se intenta
  descontar si falta stock.

- **Historial: "¿cómo se hizo?"** (2026-07-15): cada `produce` asienta un snapshot
  inmutable por ingrediente en la tabla nueva `production_run_items` (migración 008):
  `supply_name`, `unit`, `location_code`, `quantity_consumed`, `unit_cost` y
  `batch_breakdown` (JSONB con los lotes FIFO consumidos: `batch_code`/`expiration_date`/
  `quantity`). Es un SNAPSHOT (se copia al producir), no lectura en vivo: el historial
  sigue siendo legible aunque el insumo, su ubicación o sus lotes cambien o se borren.
  Se expone en `GET /api/v1/production/{id}/preparation` (ADMIN+, 404 vía
  `ProductionRunNotFoundError`) y se abre desde un modal en el historial del frontend
  (`PreparationButton`). Las unidades se muestran abreviadas (`UNIT_ABBR`) para evitar el
  "¿0,25 de qué?".

## Fuentes que lo mencionan
- [[fuentes/sesion-backend-completo-16-hu]] — verificado: rollback deja el stock intacto

## Perspectivas/decisiones
STAFF+ puede producir (no requiere ADMIN), reflejando que la producción es una
operación operativa de cocina. Un único lock por producción (`lock:production:{recipe_id}`)
evita deadlocks entre ingredientes.

## Contradicciones detectadas
Ninguna.
