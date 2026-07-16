---
title: "Temas de color con variables CSS y Tailwind"
tags: [frontend, tailwind, css, temas, branding]
source_count: 1
---

# Temas de color con variables CSS y Tailwind

## Definición
Técnica para cambiar la paleta de una app Tailwind **en tiempo de ejecución**, sin
recompilar, resolviendo los colores desde variables CSS en vez de valores literales.

## El problema
Tailwind compila las clases estáticamente. Con `brand: { 500: "#f83b7e" }` en el config,
`bg-brand-500` queda grabado en el CSS. Cambiar de paleta exigiría recompilar.

## La solución
1. **`tailwind.config.ts`** resuelve cada tono a una variable:
   ```ts
   brand[shade] = `rgb(var(--brand-${shade}) / <alpha-value>)`
   ```
2. **`globals.css`** define las paletas como **canales RGB sueltos**, no como `#hex` ni
   `rgb(...)`:
   ```css
   :root, :root[data-theme="rosa"] { --brand-500: 248 59 126; }
   :root[data-theme="menta"]       { --brand-500: 15 157 118; }
   ```
3. **El layout raíz** estampa `<html data-theme={settings.theme}>` leyendo
   [[conceptos/configuracion-sistema-en-bd]].

## Por qué canales sueltos
El formato `"R G B"` es obligatorio para que `<alpha-value>` siga funcionando. Con él,
`bg-brand-500` compila a `rgb(var(--brand-500) / var(--tw-bg-opacity))` y clases con
transparencia como `bg-brand-50/40` o `ring-brand-200` siguen intactas. Con `#hex` o
`rgb()` completo, la opacidad se rompe.

## Paletas disponibles
`rosa` (pastel, por defecto) · `chocolate` · `menta` · `azul`. Cada una define los 10 tonos
50–900. Los slugs deben coincidir con el enum `ThemeName` del backend.

## Lo que NO cubre
Solo tematiza los tonos `brand`. Las superficies neutras (`bg-white`, `text-slate-800`,
`.card`, `.input`) siguen fijas, así que **no hay modo oscuro**: implementarlo exigiría
revisar cada superficie blanca en ~25 archivos.

## Fuentes que lo mencionan
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — implementación y verificación

## Perspectivas/decisiones
Se descartó el color libre con selector: derivar 10 tonos por interpolación desde un color
base rompe el contraste del texto con bases muy claras u oscuras. Cuatro paletas curadas con
contraste verificado son más seguras que la libertad total.

## Contradicciones detectadas
Ninguna.
