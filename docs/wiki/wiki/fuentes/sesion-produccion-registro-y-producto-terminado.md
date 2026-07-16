---
title: "Sesión: registro de producción y producto terminado (HU-17)"
date: 2026-07-10
source_url: ""
source_path: ""
type: sesion
tags: [hu-17, produccion, producto-terminado, migracion, tests, sdd]
---

# Sesión: registro de producción y producto terminado (HU-17)

## Resumen
El usuario final (dueño de la pastelería) reportó que al producir una receta "no se sabe dónde
queda registrado" lo producido. Al auditar el flujo se confirmó el vacío: `ProductionService.produce`
descontaba insumos (un EXIT por ingrediente) pero **no registraba la corrida ni el producto
terminado**. Como la pastelería guarda tortas en refri para venderlas después (colchón de alta
demanda), el producto terminado debe ser inventario. Se implementó **HU-17** siguiendo SDD:
primero el spec, luego código, luego verificación.

## Ideas clave
- El producto terminado se modela **reutilizando `supply_items`** con `item_type =
  FINISHED_PRODUCT`; hereda lotes, FIFO, vencimiento, movimientos y valorización.
- Producir ahora, en una sola transacción: EXIT de insumos (FIFO) + **ENTRY del producto** (crea
  lote con vencimiento = hoy + `shelf_life_days`) + asiento en **`production_runs`** (inmutable).
- Vender después = EXIT normal del producto; el FIFO consume primero lo más próximo a vencer.
  No hizo falta módulo de pedidos (fuera de alcance MVP).
- Decisiones confirmadas con el usuario: producto creado manualmente y referenciado por la receta;
  venta como salida simple.

## Cambios (superficie)
- **Spec:** HU-17 (4 escenarios) en `user-stories.md`; RF-17, índice, `04-tasks` (Bloque 13,
  9 tareas), `06-traceability` en `docs/spec/`.
- **Backend:** `ItemType`; migración `007` (`item_type`, `recipes.produces_supply_item_id` +
  `shelf_life_days`, tabla `production_runs`); `ProductionRunModel`; `ProductionRunRepository`;
  `ProductionService.produce` (fases 3–4) + `list_production_history`; `GET /production/history`.
- **Frontend:** toggle "producto terminado" en alta de insumo; `RecipeForm` elige producto +
  vida útil; tabla de historial de producción.

## Verificación
- Migración `007` aplicada a la BD de desarrollo y a `pastry_test` (vía `scripts/setup_test_db.py`).
- Suite completa **verde: 121 tests, cobertura 88%**. Se añadió un test unitario
  (`test_production_registers_finished_product_and_run`) y uno de integración end-to-end
  (`test_production_registers_finished_product_stock_and_history`) que produce contra Postgres
  real y comprueba stock del producto +10 e historial.
- De paso se corrigieron 2 tests de reportes preexistentes (no contemplaban el BOM UTF-8 que la
  exportación CSV antepone desde 2026-07-09) — ver [[conceptos/olap-export-desnormalizado]].

## Entidades mencionadas
- [[entidades/pastrystock-manager]] — proyecto
- [[entidades/backend-pastrystock]] — capa modificada

## Conceptos relacionados
- [[conceptos/producto-terminado-y-registro-de-produccion]] — concepto central de esta sesión
- [[conceptos/produccion-bom-transaccion-atomica]] — base atómica reutilizada
- [[conceptos/fifo-lotes-vencimiento]] — FIFO aplicado también a productos terminados
- [[conceptos/aislamiento-bd-tests]] — la BD de test necesitó re-migrarse

## Notas de síntesis
Cambio gobernado por SDD: el spec precedió al código y la matriz de trazabilidad quedó cerrada
para HU-17, reforzando la evidencia metodológica del proyecto.
