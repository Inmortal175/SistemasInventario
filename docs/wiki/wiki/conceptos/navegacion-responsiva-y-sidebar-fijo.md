---
title: "Navegación responsiva y sidebar fijo"
tags: [frontend, responsive, css, flexbox, ux, accesibilidad]
source_count: 1
---

# Navegación responsiva y sidebar fijo

## Definición
Dos correcciones de layout: dar navegación a los anchos móviles (donde no existía) y anclar
el menú lateral al viewport para que no crezca con el contenido.

## El móvil no tenía navegación
El `<aside>` era `hidden w-64 … md:flex` **sin ninguna alternativa**. Por debajo de 768 px
la aplicación se quedaba literalmente sin menú: no había forma de ir de una sección a otra.

Solución: `MobileNav.tsx`, una barra superior `sticky` con hamburguesa y un drawer lateral
que reutiliza el `Sidebar` existente. Se cierra al navegar (efecto sobre `usePathname`) y
bloquea el scroll del fondo (`document.body.style.overflow`), que en iOS y Android seguía
desplazándose bajo el overlay.

## El menú crecía hacia abajo
Causa: el `<aside>` es un hijo flex y, por defecto (`align-items: stretch`), se estira a la
altura del contenedor. Cuando la tabla crecía, el menú crecía con ella y el bloque de perfil
con "Cerrar sesión" se hundía fuera de la pantalla.

Solución: `h-screen` + `sticky top-0`. La altura explícita anula el estirado y el elemento
queda anclado al viewport. Además, el `<nav>` interno lleva `flex-1 overflow-y-auto`: si
algún día hay más entradas que alto de pantalla, scrollea el nav y no la página, dejando el
logo y el perfil siempre visibles.

## Otros ajustes de la misma tanda
- El `<main>` pasó de `mx-auto max-w-5xl` a `max-w-6xl`.
- Padding progresivo: `px-4 py-6 sm:px-5 sm:py-8 md:px-10`.
- Footer con copyright, en su propio contenedor apilado.

## Fuentes que lo mencionan
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — implementación y verificación

## Perspectivas/decisiones
El drawer móvil importa el mismo componente `Sidebar` que el escritorio, así que las
entradas de navegación y su filtrado por rol ([[conceptos/rbac]]) viven en un solo sitio.

## Contradicciones detectadas
Ninguna.
