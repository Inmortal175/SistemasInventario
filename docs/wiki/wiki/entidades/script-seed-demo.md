---
title: "Script seed_demo.py"
type: herramienta
tags: [seed, demo, datos-simulacion, fifo, recetas]
---

# Script `seed_demo.py`

## Descripción
Siembra un escenario completo y coherente para demos y pruebas manuales, alrededor de la
receta **Torta de Chocolate**. Vive en `backend/scripts/seed_demo.py`. Complementa a
[[entidades/script-seed-admin]], que solo crea el primer usuario.

```bash
docker-compose exec backend python scripts/seed_demo.py --cakes 3
```

## Qué siembra
- **4 categorías** con ícono y color: Secos y Harinas, Lácteos y Frescos, Chocolatería,
  Aditivos y Esencias.
- **6 ubicaciones** rotuladas: `ALM-01`, `EST-01-F1`, `EST-02`, `REF-01`, `FRZ-01`, `CAB-01`.
- **10 insumos** con SKU prefijado `DEMO-`, precios en soles y proveedores reales del rubro.
- **Lotes perecederos** para chocolate, huevos, mantequilla y leche. Uno de huevos vence en
  5 días y uno de leche en 7, para que el cron de vencimiento (HU-13-03) tenga algo real que
  reportar en la demo.
- **La receta** *Torta de Chocolate* (molde 22 cm, 8 porciones, 10 ingredientes).
- **41 movimientos**: la compra inicial de cada insumo, tres tortas ya producidas descontadas
  por FIFO real, y una merma de huevos.

## Invariantes verificadas
- El stock de cada insumo con lotes **coincide exactamente** con la suma de sus lotes activos.
- Ningún stock ni lote queda negativo.
- Idempotente: la segunda corrida escribe 0 movimientos. La guarda es la presencia de la
  merma de huevos, que es el último registro que escribe la función; sin ella, una segunda
  corrida volvería a descontar stock. Ver [[conceptos/seed-idempotente]].

## Notas de diseño
- No borra nada: `movement_history` es inmutable por diseño, así que el script no ofrece
  `--reset`.
- Replica el FIFO de `ProductionService` en una función local (`_consume_fifo`) en vez de
  instanciar el servicio completo con Redis y alertas.
- Escribe directo en PostgreSQL, así que tras correrlo conviene invalidar las claves Redis
  `categories:active:all`, `supplies:page:*` y `dashboard:kpis`.
- Los `icon_name` de las categorías deben pertenecer a la lista blanca del backend
  (ver [[conceptos/iconos-fontawesome-nextjs]]).

## Aparece en
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — creación y verificación

## Relaciones
- [[entidades/backend-pastrystock]] — usa sus modelos y repositorios
- [[entidades/script-seed-admin]] — requisito previo (debe existir un usuario)
- Aplica [[conceptos/fifo-lotes-vencimiento]] y [[conceptos/seed-idempotente]]

## Notas
Si no encuentra el SUPERADMIN configurado, usa el usuario activo más antiguo como autor de
todos los registros.
