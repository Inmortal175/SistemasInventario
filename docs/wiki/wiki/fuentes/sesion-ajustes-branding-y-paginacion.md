---
title: "Sesión: Ajustes del sistema, branding, recorte de imágenes y paginación"
date: 2026-07-09
source_url: ""
source_path: "conversación de trabajo (Claude Code)"
type: sesion-desarrollo
tags: [ajustes, branding, temas, uploads, recorte-imagenes, paginacion, responsive, docker, redis]
---

# Sesión: Ajustes del sistema, branding, recorte de imágenes y paginación

## Resumen
Sesión larga que convirtió al sistema en algo configurable de verdad. Partió de un bug de
usuarios suspendidos, pasó por datos de simulación, responsive y paginación, y terminó
construyendo un módulo completo de **Ajustes** (`/settings`, solo SUPERADMIN) con nombre,
logo, temas de color, fondos de login por dispositivo, recorte de imágenes y reglas de
negocio. De paso emergieron dos hallazgos de infraestructura que costaban tiempo cada día.

Estado final: **119 tests** en verde, cobertura **82.6%**, typecheck del frontend limpio.
Migraciones aplicadas: **004** (system_settings), **005** (fondos de login), **006**
(reglas de negocio e identidad fiscal).

## Ideas clave

- **Un botón que existía y nunca podía usarse.** `PATCH /users/{id}/reactivate`, el
  servicio y el botón "Reactivar" estaban completos, pero `list_users()` llamaba a
  `list_active()`: al suspender a alguien desaparecía de la tabla y no había forma de
  devolverle el acceso. Se añadió `UserRepository.list_all()`. Ver [[conceptos/rbac]].

- **La foto de perfil no aparecía en el menú** por una causa distinta a la esperada: el
  proxy de subida devolvía la nueva `avatar_url` pero nunca reescribía la **cookie de
  sesión**, de donde el sidebar lee el avatar. Ver [[conceptos/avatar-perfil-y-estaticos]].

- **El `content-type` lo declara el cliente.** Decodificar la imagen con Pillow es lo único
  que prueba que un archivo es una imagen. Un `<?php system($_GET["c"]); ?>` declarado como
  `image/png` ahora responde 422 sin escribir nada en disco. Ver
  [[conceptos/recorte-imagenes-1a1-y-aspecto]].

- **Los temas se resuelven en tiempo de ejecución, no de compilación.** Los colores `brand`
  pasaron a variables CSS con canales RGB sueltos, de modo que cambiar de paleta no exige
  recompilar Tailwind y `bg-brand-50/40` sigue funcionando. Ver
  [[conceptos/temas-css-variables-tailwind]].

- **El umbral de vencimiento no es infraestructura.** Vivía en `EXPIRATION_ALERT_DAYS` y
  cambiarlo exigía reiniciar el contenedor. "Avísame cinco días antes" es una decisión del
  negocio: migró a `system_settings`. Ver [[conceptos/configuracion-sistema-en-bd]].

- **Una caché puede tumbar la API tras una migración.** Al agregar campos al schema,
  `GET /settings` devolvía 500 porque Redis tenía la forma anterior del objeto. Ver
  [[conceptos/cache-obsoleta-tras-cambio-de-schema]].

- **El hot-reload del frontend nunca funcionó en este entorno.** Los bind-mounts de Docker
  en Windows no emiten eventos inotify. Ver [[conceptos/hot-reload-docker-windows]].

## Trabajo realizado (orden cronológico)

### 1. Usuarios suspendidos reactivables
- `UserRepository.list_all()` + `IUserRepository`; `UserService.list_users()` deja de filtrar.
- Log de auditoría simétrico: `USER_REACTIVATED`.

### 2. Datos de simulación — Torta de Chocolate
- Nuevo `backend/scripts/seed_demo.py` ([[entidades/script-seed-demo]]): 4 categorías,
  6 ubicaciones, 10 insumos, lotes perecederos, la receta *Torta de Chocolate* (molde 22 cm,
  8 porciones) y 41 movimientos (compra inicial, 3 tortas producidas por FIFO real, 1 merma).
- Idempotente y verificado: stock de cada insumo = suma de sus lotes activos, sin negativos.

### 3. Responsive y estética del menú
- `MobileNav` (hamburguesa + drawer) — antes, por debajo de 768 px la app **no tenía
  navegación**: el `<aside>` era `hidden md:flex` sin alternativa.
- El `<main>` pasó de `max-w-5xl` a `max-w-6xl`.
- Footer con copyright "© {año} Franklin Figueroa Pérez".
- Menú fijo: el `<aside>` es hijo flex y se estiraba con la tabla; `h-screen` + `sticky top-0`
  lo anclan. Ver [[conceptos/navegacion-responsiva-y-sidebar-fijo]].

### 4. Paginación
- Componente `Pagination` (enlaces reales con `?page=N`, no estado de cliente).
- Aplicada a insumos, historial de movimientos de un insumo (`?mpage=`) y auditoría de
  usuario (paginación nueva en el backend, en memoria). Ver
  [[conceptos/paginacion-ui-searchparams]].

### 5. Ajustes del sistema
- Tabla `system_settings` de fila única (CHECK `id = 1`), migraciones 004/005/006.
- Selector de iconos de categoría en modal, con **lista blanca validada en el backend**.
- Nombre, logo, 4 paletas de color, fondos de login por dispositivo, velo ajustable,
  moneda/locale, tamaño de página, umbral de vencimiento e identidad fiscal.
- `GET /api/v1/settings` es **público**: el login necesita la marca antes de que exista sesión.

### 6. Recorte de imágenes
- Recortador propio en canvas (sin dependencias nuevas en el frontend), con pan, zoom y
  proporción configurable. El backend re-normaliza con Pillow (`ImageOps.fit`).

### 7. Cierre de detalles
- Favicon desde el logo; footer con nombre configurado y año calculado.
- `/docs` y `/openapi.json` ahora muestran el nombre real (antes decían "PastryStock Manager"
  mientras la interfaz decía otra cosa).
- Avatar recortado 1:1 (256 px).

## Entidades mencionadas
- [[entidades/pastrystock-manager]] — proyecto
- [[entidades/backend-pastrystock]] — settings, uploads, paginación de auditoría
- [[entidades/frontend-nextjs]] — /settings, MobileNav, Pagination, ImageCropper
- [[entidades/script-seed-demo]] — nuevo seed de simulación

## Conceptos relacionados
- [[conceptos/configuracion-sistema-en-bd]] — nuevo
- [[conceptos/temas-css-variables-tailwind]] — nuevo
- [[conceptos/recorte-imagenes-1a1-y-aspecto]] — nuevo
- [[conceptos/fondo-login-responsivo]] — nuevo
- [[conceptos/paginacion-ui-searchparams]] — nuevo
- [[conceptos/navegacion-responsiva-y-sidebar-fijo]] — nuevo
- [[conceptos/hot-reload-docker-windows]] — nuevo
- [[conceptos/cache-obsoleta-tras-cambio-de-schema]] — nuevo
- [[conceptos/avatar-perfil-y-estaticos]] — actualizado (bug de cookie, recorte 1:1)
- [[conceptos/iconos-fontawesome-nextjs]] — actualizado (selector + lista blanca)
- [[conceptos/seed-idempotente]] — actualizado (seed_demo)
- [[conceptos/cache-first-paginacion]] — actualizado (caché de settings)
- [[conceptos/rbac]] — Ajustes es exclusivo de SUPERADMIN

## Citas destacadas
> "El `content_type` lo declara el cliente, así que decodificar con Pillow es lo único que
> prueba que el archivo es una imagen." — comentario en `app/core/uploads.py`

> "El umbral de días para la alerta de vencimiento vive ahora en
> `system_settings.expiration_alert_days`: lo decide la pastelería, no el despliegue."
> — comentario en `app/core/config.py`

## Notas de síntesis
Tres decisiones de frontera se repitieron y conviene recordarlas:

1. **Negocio vs. despliegue.** El umbral de vencimiento, la moneda y el tamaño de página
   son del negocio → base de datos. El rate limiting del login y la expiración del token
   son de operación → variables de entorno. Exponer los segundos en la interfaz invita a
   desactivar la protección contra fuerza bruta sin entender las consecuencias.

2. **El cliente propone, el servidor dispone.** El recorte lo elige el usuario en el
   navegador, pero el servidor lo re-aplica. Vale para el 1:1 del logo, para las
   proporciones de los fondos y para el avatar.

3. **Una sola fuente de verdad por dato.** `config.app_name` y `system_settings.app_name`
   competían; ganó la base de datos, y `/docs` se alinea al arrancar y en cada PATCH.

Pendiente identificado y no resuelto: `getSupply()` en `lib/queries.ts` busca un insumo
pidiendo el listado con `limit: 100` y filtrando en memoria (no existe `GET /supplies/{id}`).
Funciona hoy con 10 insumos; pasará a dar 404 al superar los 100.
