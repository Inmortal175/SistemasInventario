---
title: "Exportación OLAP desnormalizada (CSV)"
tags: [olap, etl, reportes, csv, desnormalizacion]
source_count: 1
---

# Exportación OLAP desnormalizada (CSV)

## Definición
Endpoint que aplana el esquema transaccional 3NF a una vista de hechos plana (un registro
por movimiento) lista para ingestión ETL en un almacén de datos (PowerBI, ClickHouse) — HU-12.

## Implementación
- `MovementRepository.export_denormalized(start_date)`: JOIN de `movement_history` +
  `users` + `supply_items` + `dynamic_categories` + `locations`.
- `ReportService.export_csv`: genera CSV con las columnas exactas exigidas:
  `[movement_id, timestamp, user_id, user_role, user_email, supply_id, supply_name,
  category_name, location_code, movement_type, quantity, stock_before, stock_after,
  is_adjustment, adjustment_reason]`.
- `GET /api/v1/reports/export?format=csv&start_date=` (ADMIN+, STAFF→403). Devuelve
  `Content-Disposition: attachment; filename=inventory_olap_export.csv`.

## Fuentes que lo mencionan
- [[fuentes/sesion-backend-completo-16-hu]] — verificado: cabeceras y columnas correctas

## Perspectivas/decisiones
`is_adjustment` se deriva del `movement_type` (ADJUSTMENT_ADD/SUB); `adjustment_reason`
reutiliza la columna `notes` cuando el movimiento es un ajuste. Modelo en estrella
(DimUsers, DimSupplies, DimLocations, FactMovements) descrito en `docs/user-stories.md`.

## Contradicciones detectadas
Ninguna.
