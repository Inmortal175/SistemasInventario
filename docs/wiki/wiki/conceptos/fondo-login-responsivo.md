---
title: "Fondo del login responsivo por dispositivo"
tags: [frontend, responsive, imagenes, login, branding, accesibilidad]
source_count: 1
---

# Fondo del login responsivo por dispositivo

## Definición
Tres imágenes de fondo del login, una por familia de dispositivo, cada una con su propio
recorte y su propia proporción, servidas por `<picture>` según el ancho del viewport.

## Breakpoints y proporciones
| Dispositivo | Ancho | Proporción | Salida |
|---|---|---|---|
| Móvil | < 768 px | 9:16 | 720×1280 |
| Tablet | 768–1023 px | 3:4 | 900×1200 |
| Escritorio | ≥ 1024 px | 16:9 | 1920×1080 |

Coinciden con `md:` y `lg:` de Tailwind, que es donde el resto de la interfaz ya cambia de
forma (el sidebar aparece en `md`).

## Cadena de respaldo
Cada tamaño cae al inmediatamente mayor: móvil → tablet → escritorio. Subir solo la imagen
de escritorio ya cubre los tres dispositivos. Sin ninguna, no se renderiza el bloque y el
login queda con el fondo liso.

```tsx
const desktop = assetUrl(settings.login_bg_desktop_url);
const tablet  = assetUrl(settings.login_bg_tablet_url) ?? desktop;
const mobile  = assetUrl(settings.login_bg_mobile_url) ?? tablet;
```

## Legibilidad
Velo `bg-slate-900` con opacidad configurable (0–80 %, por defecto 40 %) sobre la foto. El
formulario sigue en su tarjeta blanca opaca; el título y el pie pasan a texto blanco con
sombra solo cuando hay fondo. Así el texto se lee con cualquier imagen, sin configurar nada.

La opacidad va en `style` y no en una clase de Tailwind, porque las clases se compilan
estáticamente (misma razón que en [[conceptos/temas-css-variables-tailwind]]).

## Detalle de apilamiento
El bloque del fondo usa `absolute inset-0` dentro de un contenedor `relative`, con el
`<main>` y el pie en `relative z-10`. Un `z` negativo quedaría **detrás del color de fondo
que el `<body>` propaga al lienzo**.

## Fuentes que lo mencionan
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — diseño y verificación

## Perspectivas/decisiones
Se descartó "una sola imagen 16:9 recortada por CSS": en móvil vertical se recorta sola y
suele perder el motivo central. También se descartó la tarjeta de vidrio esmerilado
(glassmorphism): el contraste del texto dependería de la foto que suba el usuario.

## Contradicciones detectadas
Ninguna. Las imágenes se recortan con [[conceptos/recorte-imagenes-1a1-y-aspecto]] y se
guardan en [[conceptos/configuracion-sistema-en-bd]].
