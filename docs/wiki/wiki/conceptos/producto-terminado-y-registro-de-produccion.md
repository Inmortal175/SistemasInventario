---
title: "Producto terminado y registro de producción (HU-17)"
tags: [produccion, producto-terminado, inventario, fifo, bom, auditoria, hu-17]
source_count: 1
---

# Producto terminado y registro de producción (HU-17)

## Definición
Antes de HU-17, producir una receta (HU-15) descontaba los insumos pero **no dejaba rastro de lo
producido**: la cantidad viajaba en la respuesta HTTP y se perdía. HU-17 cierra ese vacío
haciendo que el **producto terminado sea inventario** y que **cada corrida de producción quede
registrada** de forma inmutable.

## Motivación (usuario final)
El dueño de la pastelería produce tortas y las **guarda en refrigeración** para venderlas
después; en días de alta demanda (p. ej. 100 pedidos) usa lo producido días antes como colchón.
Por tanto el producto terminado tiene stock, ubicación (REF), vencimiento y se descuenta al
venderse — no basta con contar consumos de materia prima.

## Decisiones de diseño
- **Reutilizar `supply_items`**: un producto terminado es un `supply_item` con
  `item_type = FINISHED_PRODUCT` (default `INGREDIENT`). Así hereda stock, lotes FIFO,
  vencimiento, movimientos y valorización sin duplicar modelo. Ver [[conceptos/fifo-lotes-vencimiento]].
- `item_type` se guarda como **texto + CHECK** (`native_enum=False`), no como ENUM nativo de PG,
  para no migrar un tipo (misma filosofía que los temas de color).
- **UX separada del dato (feedback del usuario, 2026-07-11):** aunque el dato vive en
  `supply_items`, el producto **no se registra como insumo**. La **receta lo auto-crea**
  (`product_name`, `product_location_id`, `shelf_life_days`) bajo la categoría "Productos
  terminados", y se muestra en su **propia sección** (el listado de insumos filtra
  `item_type = INGREDIENT` vía el parámetro `item_type` de `GET /supplies`). Se descartó una
  tabla `products` separada por no duplicar el motor de inventario ni fragmentar auditoría/OLAP.
- La receta enlaza el producto que genera (`recipes.produces_supply_item_id`) y su vida
  útil (`shelf_life_days`), con los que se fija el `expiration_date` del lote producido.
- Nueva tabla **inmutable `production_runs`** (como `movement_history`): receta, producto,
  cantidad, lote generado, costo total de insumos, ejecutor y fecha.
- **Atomicidad**: producir corre en una sola transacción — descuento FIFO de insumos (EXIT) +
  ENTRY del producto (crea lote) + asiento en `production_runs`. Si falta un ingrediente, el
  ROLLBACK deja todo intacto (hereda de [[conceptos/produccion-bom-transaccion-atomica]]).
- **Vender = EXIT del producto**: no requiere lógica nueva; el FIFO consume primero lo más
  próximo a vencer. Un módulo de "pedidos" de primera clase quedó fuera de alcance (MVP).

## Superficie técnica
- Dominio: `ItemType`. Modelos: `supply_items.item_type`, `recipes.produces_supply_item_id` +
  `shelf_life_days`, `ProductionRunModel`. Migración `007`.
- Servicio: `ProductionService.produce` (fases 3–4) + `list_production_history`.
  Repo `ProductionRunRepository`. Endpoint `GET /production/history` (ADMIN+).
- Frontend: toggle "producto terminado" en alta de insumo; receta elige producto + vida útil;
  tabla de historial de producción en `/production`.

## Fuentes que lo mencionan
- [[fuentes/sesion-produccion-registro-y-producto-terminado]] — implementación completa por SDD

## Contradicciones detectadas
Ninguna. Extiende [[conceptos/produccion-bom-transaccion-atomica]] y se apoya en
[[conceptos/fifo-lotes-vencimiento]] y [[conceptos/valorizacion-inventario]].
