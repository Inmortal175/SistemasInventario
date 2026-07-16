---
title: "Valorización financiera del inventario"
tags: [finanzas, valorizacion, costos, mermas, proveedores]
source_count: 1
---

# Valorización financiera del inventario

## Definición
Cálculo del valor monetario de los activos en almacén y de la pérdida acumulada por
mermas, a partir del costo unitario de cada lote y su proveedor (HU-16).

## Fórmulas
- Valor total de activos: `V_total = Σ (current_stock_i × unit_cost_i)` sobre lotes activos.
- Pérdida por mermas: `Loss_total = Σ (quantity_wasted_j × unit_cost_batch_j)` sobre
  movimientos WASTE en el período consultado.

## Implementación
- `supply_batches` guarda `unit_cost` y `vendor_name`; el alta de lote registra un
  movimiento ENTRY con `unit_cost` y expone `total_movement_cost = quantity × unit_cost`.
- `MovementRepository.sum_waste_cost(start_date)` suma `quantity × unit_cost` de los WASTE.
- Endpoint `GET /api/v1/dashboard/financials?start_date=` (ADMIN+) devuelve
  `{total_active_value, total_waste_loss, active_batches_count, period_start}`.

## Fuentes que lo mencionan
- [[fuentes/sesion-backend-completo-16-hu]] — verificado: 15 L × 4.5 = 67.5 de valor activo

## Perspectivas/decisiones
El costo de merma depende de que el movimiento WASTE lleve `unit_cost`. El consumo FIFO
lo calcula como promedio ponderado de los lotes tocados. Ver [[conceptos/fifo-lotes-vencimiento]].

## Contradicciones detectadas
Tras una conciliación (HU-11) el stock a nivel de insumo puede diferir de la suma de
lotes; la valorización usa el nivel de lote. Diferencia transitoria aceptada en el MVP.
