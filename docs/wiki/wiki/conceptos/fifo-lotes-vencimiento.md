---
title: "FIFO por lotes y fechas de vencimiento"
tags: [inventario, fifo, lotes, perecederos, concurrencia]
source_count: 1
---

# FIFO por lotes y fechas de vencimiento

## Definición
Metodología de despacho que consume primero los lotes que vencen antes (First-In para
perecederos = el más próximo a expirar). Cada insumo perecedero tiene N lotes
(`supply_batches`) con `current_stock`, `unit_cost`, `vendor_name` y `expiration_date`.
El stock total del insumo = Σ `current_stock` de lotes activos.

## Implementación (HU-13)
- Repositorio `BatchRepository.list_active_fifo_for_update`: ordena por
  `expiration_date ASC NULLS LAST`, luego `created_at ASC`, con `with_for_update()`
  para bloquear las filas durante el descuento.
- `BatchService.consume_fifo`: valida que Σ lotes ≥ cantidad (si no,
  `InsufficientStockError`), descuenta secuencialmente, desactiva el lote que llega a 0,
  recalcula el total del insumo y registra **un solo** movimiento con el desglose por
  lote en `notes`. Dispara alerta si el total cae bajo el mínimo.
- Alerta predictiva (HU-13-03): `scan_expiring_batches` busca lotes que vencen dentro de
  `EXPIRATION_ALERT_DAYS` (5 por defecto), publica en `alerts:expiration_critical` y
  marca `alert_sent=true` para no repetir. Ejecutable vía `scripts/check_expirations.py`.

## Fuentes que lo mencionan
- [[fuentes/sesion-backend-completo-16-hu]] — implementación y verificación E2E

## Perspectivas/decisiones
El costo unitario del movimiento de consumo se calcula como promedio ponderado de los
lotes tocados (Σ consumido_i × costo_i / cantidad), y se guarda en
`movement_history.unit_cost` para alimentar la pérdida por mermas de [[conceptos/valorizacion-inventario]].

## Contradicciones detectadas
Ninguna. Reutilizado por [[conceptos/produccion-bom-transaccion-atomica]].
