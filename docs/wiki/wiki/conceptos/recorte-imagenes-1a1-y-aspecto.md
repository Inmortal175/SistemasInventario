---
title: "Recorte de imágenes: canvas en el cliente, Pillow en el servidor"
tags: [uploads, imagenes, canvas, pillow, seguridad, frontend, backend]
source_count: 1
---

# Recorte de imágenes: canvas en el cliente, Pillow en el servidor

## Definición
Patrón de doble capa para subir imágenes con proporción garantizada: el usuario **elige el
encuadre** en el navegador y el servidor **impone la invariante**, recortando al centro si
hace falta.

## Cliente: `ImageCropper.tsx`
Componente propio, **sin dependencias nuevas** (no se añadió `react-easy-crop` ni similar).

- Recuadro con `aspect-ratio` configurable; pan con Pointer Events (funciona con dedo) y
  zoom con deslizador.
- Al confirmar, un `<canvas>` extrae exactamente la región visible y produce el archivo.
- Salida configurable: PNG para el logo y el avatar (conserva transparencia), JPEG q0.85
  para los fondos (una foto 1920×1080 en PNG pesa megabytes).

### Dos trampas resueltas
1. **`aspect-ratio` exige que solo una dimensión esté fijada.** En apaisado manda el ancho;
   en vertical, el alto. Con ambas fijas, un recuadro 9:16 desbordaba la pantalla.
2. **El encuadre inicial necesita el tamaño natural Y el del recuadro**, y no hay garantía
   de cuál llega primero: `onLoad` y el `ResizeObserver` corren sueltos. Calcularlo dentro
   de `onLoad` funcionaba a veces. Se movió a un efecto que espera a ambos.
3. JPEG no tiene canal alfa: sin rellenar el canvas de blanco antes de dibujar, una PNG
   transparente sale con fondo negro.

## Servidor: `app/core/uploads.py`
`save_fitted_image(file, subdir, stem, size, fmt, max_bytes)` con `ImageOps.fit` (Pillow):

- **Valida decodificando.** El `content_type` lo declara el cliente; abrir la imagen con
  Pillow es lo único que prueba que lo es. Un archivo con `<?php system($_GET["c"]); ?>`
  declarado `image/png` responde **422 sin escribir nada en disco**.
- **Corrige la orientación EXIF** (`ImageOps.exif_transpose`) antes de recortar: las fotos
  de celular guardan la rotación ahí, y el recorte se calcularía sobre otra orientación.
- **Center-crop** a la proporción exacta: cubre a quien llame a la API sin pasar por la UI.
- **Borra el archivo que reemplaza** (`delete_static_file`), validando que la ruta esté
  dentro de `static/`. Sin esto, cada cambio de logo dejaba el anterior huérfano.

## Tamaños normalizados
| Uso | Salida | Formato |
|---|---|---|
| Logo | 512×512 | PNG |
| Avatar | 256×256 | PNG |
| Fondo móvil | 720×1280 (9:16) | JPEG |
| Fondo tablet | 900×1200 (3:4) | JPEG |
| Fondo escritorio | 1920×1080 (16:9) | JPEG |

Límite de subida: 2 MB para logo/avatar, **8 MB para fondos** (2 MB rechazaría fotos
legítimas de pantalla completa).

## Fuentes que lo mencionan
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — implementación y pruebas de seguridad

## Perspectivas/decisiones
El recorte solo en el navegador es una sugerencia, no una garantía: cualquiera con el token
puede llamar al endpoint directo. La invariante la impone el servidor. Verificado subiendo
una imagen 600×200 con tres franjas de color: el resultado fue 512×512 y **todo del color
central** — recorte centrado, no imagen aplastada.

## Contradicciones detectadas
Ninguna. Reemplazó a la validación anterior descrita en
[[conceptos/avatar-perfil-y-estaticos]], que tomaba la extensión del nombre de archivo
enviado por el cliente.
