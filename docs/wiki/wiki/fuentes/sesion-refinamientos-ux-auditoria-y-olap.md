---
title: "Sesión: refinamientos de UX (producto), auditoría legible y OLAP"
date: 2026-07-11
source_url: ""
source_path: ""
type: sesion
tags: [hu-17, hu-12, hu-10, auditoria, ux, olap, producto-terminado]
---

# Sesión: refinamientos de UX (producto), auditoría legible y OLAP

## Resumen
Tras usar HU-17, el usuario final planteó tres inquietudes: (1) registrar el producto terminado
como "insumo" es tedioso y conceptualmente incorrecto; (2) la auditoría de movimientos se lee como
código ("EXIT de 0.240 (stock 3.680→3.440)"), no en español; (3) dudas sobre el export OLAP. Se
resolvieron las tres por SDD.

## Cambios
- **Producto terminado (HU-17):** ahora la **receta auto-crea** el producto (`product_name`,
  `product_location_id`, `shelf_life_days`) bajo la categoría "Productos terminados" — ya no se
  registra como insumo. Se creó una **sección propia "Productos terminados"** (nav + página) y el
  listado de insumos filtra `item_type = INGREDIENT` (nuevo parámetro `item_type` en
  `GET /supplies`, propagado a repo, servicio y clave de caché). Se quitó el toggle del alta de
  insumo y el select de la receta.
- **Auditoría legible (HU-10-03):** el resumen se arma en español con verbo, nombre del insumo,
  unidad y motivo ("Salida de 0.24 kg de Harina · Producción de Torta de Chocolate"), vía un join
  nuevo `list_by_performer_with_context`. El frontend muestra la acción con etiqueta en español.
- **OLAP (HU-12):** el export desnormalizado gana columnas `item_type`, `unit_cost`, `total_cost`
  y `notes` — habilita análisis financiero y separar producción de consumo. Se confirmó que el
  export es una **tabla de hechos lista para ETL** (no un cubo en vivo), correcto para la HU-12.

## Ideas clave
- Separar **UX del modelo de datos**: el producto sigue en `supply_items` (motor unificado:
  FIFO, auditoría, valorización, OLAP) pero se presenta y crea como algo distinto de un insumo.
- La legibilidad de la auditoría era un problema de capa de presentación mal ubicada (enum crudo
  en el resumen del backend); se corrigió con etiquetas en español.

## Verificación
- Suite completa **verde: 121 tests, cobertura 88%**. Typecheck del frontend sin errores nuevos.
- Se actualizó el test de integración de HU-17 al nuevo flujo (receta auto-crea el producto y se
  comprueba que aparece en productos y no en insumos).

## Entidades mencionadas
- [[entidades/pastrystock-manager]] — proyecto

## Conceptos relacionados
- [[conceptos/producto-terminado-y-registro-de-produccion]] — actualizado con la UX separada
- [[conceptos/olap-export-desnormalizado]] — columnas nuevas
- [[conceptos/rbac]] — el historial de producción y reportes siguen siendo ADMIN+

## Notas de síntesis
Ciclo de feedback real del usuario → ajuste gobernado por SDD (spec actualizado, código, pruebas,
trazabilidad). Refuerza que el proyecto responde a necesidades del negocio, no solo a la consigna.
