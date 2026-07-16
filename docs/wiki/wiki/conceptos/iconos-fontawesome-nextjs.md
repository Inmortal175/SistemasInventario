---
title: "Iconos FontAwesome en Next.js App Router"
tags: [frontend, nextjs, iconos, fontawesome, ux]
source_count: 2
---

# Iconos FontAwesome en Next.js App Router

## Definición
Sistema de iconografía del frontend basado en FontAwesome React con SVGs empaquetados
localmente (sin CDN), apto para el contenedor Docker offline y para la CSP estricta.

## Implementación
- Paquetes: `@fortawesome/fontawesome-svg-core`, `@fortawesome/free-solid-svg-icons`,
  `@fortawesome/react-fontawesome`.
- Componente único `src/components/Icon.tsx`: importa los iconos usados, los registra en
  un objeto `ICONS` (claves semánticas: `dashboard`, `supplies`, `production`, `batches`,
  `reconcile`, `financials`, `users`, `reports`, `alert`, `ok`…) y expone `<Icon name=…>`.
- **Clave para SSR**: `config.autoAddCss = false` + `import "@fortawesome/fontawesome-svg-core/styles.css"`
  manual. Sin esto, FA intenta inyectar su CSS en runtime y rompe el App Router.
- Instalación dentro del contenedor (node_modules es volumen anónimo):
  `pnpm add --config.store-dir=/pnpm/store/v3 …` (en Git Bash, con `MSYS_NO_PATHCONV=1`).

## Iconos de categoría: dos registros, una lista blanca (2026-07-09)
Los iconos de navegación y los de las categorías dinámicas viven en **registros separados**:

- `src/components/Icon.tsx` → `ICONS` (navegación, acciones de UI).
- `src/lib/categoryIcons.ts` → `CATEGORY_ICONS`, 38 iconos agrupados en siete familias
  (Pastelería, Lácteos y proteínas, Frutas y verduras, Bebidas y envases, Cocina, Almacén y
  limpieza, Generales), más `CATEGORY_ICON_GROUPS` para el selector.
- `src/components/CategoryIcon.tsx` devuelve `null` si el slug no está en el registro: una
  categoría antigua con un ícono retirado degrada al color plano, no rompe la página.

**El backend valida.** `backend/app/domain/category_icons.py` expone
`ALLOWED_CATEGORY_ICONS` y `CategoryCreate`/`CategoryUpdate` lo verifican con un
`field_validator`. Un ícono inventado devuelve 422 en vez de guardarse en silencio.

> Las dos listas son espejo. Si agregas uno en `categoryIcons.ts`, agrégalo también en
> `category_icons.py` o la API rechazará la categoría.

El selector (`IconPicker.tsx`) es un modal controlado: el estado del ícono se levanta al
formulario, porque `form.reset()` no limpia el estado de React de un componente hijo.

## Fuentes que lo mencionan
- [[fuentes/sesion-frontend-modulos-avanzados]] — migración de emojis a FontAwesome
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — selector de iconos y lista blanca

## Perspectivas/decisiones
Se prefirió un registro nombrado central (`ICONS`) en vez de importar iconos por página:
mantiene los imports del icon pack en un solo lugar, permite tree-shaking y desacopla los
componentes del nombre real del icono FA. Los iconos de categoría se separaron en su propio
registro porque su ciclo de vida es otro: los valida el backend y los elige el usuario.

Versión instalada: FontAwesome **7.3.0**. Cada icono es un módulo propio
(`node_modules/@fortawesome/free-solid-svg-icons/faCakeCandles.js`), así que existencia se
comprueba por archivo, no por `index.d.ts`.

## Contradicciones detectadas
Ninguna.
