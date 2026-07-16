---
title: "Paginación en la UI con searchParams"
tags: [frontend, nextjs, paginacion, server-components, ux]
source_count: 1
---

# Paginación en la UI con searchParams

## Definición
Paginación de listados mediante **enlaces reales** con `?page=N` en la URL, resuelta en
Server Components, sin estado de cliente. Complementa a
[[conceptos/cache-first-paginacion]], que es la capa de datos.

## Por qué enlaces y no estado
Con `?page=N` en la URL: se puede compartir el enlace de una página, abrirla en pestaña
nueva y usar el botón atrás del navegador. Con `useState` nada de eso funciona.

## Componente `Pagination`
- Props: `page`, `limit`, `total`, `basePath`, `param`, `query`, `noun`.
- Muestra "Mostrando 21–40 de 51 acciones", flechas anterior/siguiente y una **ventana de
  números con elipsis** que siempre deja visibles la primera y la última página.
- Si solo hay una página, no renderiza nada.
- La página 1 no lleva `?page=1`: la URL queda limpia.
- El parámetro es configurable (`param="mpage"`), de modo que dos listados en la misma
  vista no se pisen. El detalle de insumo pagina sus movimientos con `mpage` porque algún
  día querrá paginar también sus lotes.

## Vistas paginadas
| Vista | Tamaño | Fuente del límite |
|---|---|---|
| Insumos | configurable | `system_settings.page_size` |
| Auditoría de usuario | configurable | `system_settings.page_size` |
| Movimientos de un insumo | 10 | constante |

## Paginación de la auditoría
`UserService.get_audit_log(page, limit)` pagina **en memoria**, no en SQL: las entradas se
funden desde tres tablas (categorías, ubicaciones y movimientos) y el orden cronológico
global solo existe una vez unidas. El `total` sigue siendo el global, no el de la página.

## Página fuera de rango
Un marcador viejo o registros borrados llevaban a `?page=99`, que mostraba el vacío "Aún no
hay insumos registrados", como si la tabla estuviera vacía. Ahora se redirige al inicio del
listado cuando `page > 1 && items.length === 0 && total > 0`.

## Fuentes que lo mencionan
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — implementación y verificación

## Perspectivas/decisiones
Categorías, ubicaciones, usuarios y recetas **no** se paginaron: son listas acotadas por
naturaleza. El componente está listo si crecen.

## Contradicciones detectadas
Ninguna.
