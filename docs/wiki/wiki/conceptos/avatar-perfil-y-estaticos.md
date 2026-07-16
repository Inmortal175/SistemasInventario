---
title: "Avatar de perfil y archivos estáticos"
tags: [usuarios, perfil, avatar, uploads, estaticos, migraciones]
source_count: 2
---

# Avatar de perfil y archivos estáticos

## Definición
Foto de perfil por usuario: subida de imagen (JPG/PNG/WebP, máx 2 MB), almacenada en el
sistema de archivos del backend y servida como estático. Complementa
[[conceptos/gestion-perfil-usuario]].

## Implementación
- **Modelo/BD**: columna `users.avatar_url` (String 500, nullable). Migración
  `003_add_avatar_url`. `UserResponse` y `TokenResponse` exponen `avatar_url`.
- **Backend**: `POST /api/v1/auth/me/avatar` (multipart `file`) valida tipo y tamaño,
  guarda en `static/avatars/{user_id}_{rand}.ext` y persiste la ruta vía
  `UserService.update_avatar` → `UserRepository.set_avatar`. `main.py` monta
  `app.mount("/static", StaticFiles(directory="static"))`.
- **Frontend**: componente `AvatarForm` (cliente) sube por `POST /api/profile/avatar`
  (route handler que adjunta el Bearer desde la cookie httpOnly y reenvía el multipart al
  backend). El helper `assetUrl()` resuelve `/static/...` contra el origen del backend
  (NEXT_PUBLIC_API_URL sin `/api/v1`). El avatar se muestra en el perfil y en el sidebar.

## El bug: la foto no aparecía en el menú
El sidebar lee `avatar_url` de la **cookie de sesión** (`pastry_user`), no de la API. El
proxy de subida devolvía la nueva URL pero nunca reescribía esa cookie, así que
`router.refresh()` re-renderizaba con el valor viejo y la foto solo aparecía tras volver a
iniciar sesión.

Corregido en `src/app/api/profile/avatar/route.ts`: tras un 200, llama a
`updateSessionAvatar(data.avatar_url)`. Los route handlers de Next 15 pueden escribir cookies.

## Recorte 1:1 y validación real (2026-07-09)
- El avatar se muestra dentro de un círculo: sin recortar, una foto rectangular salía
  estirada. Ahora se recorta en el navegador y el servidor lo normaliza a **256×256 PNG**.
  Ver [[conceptos/recorte-imagenes-1a1-y-aspecto]].
- La implementación anterior tomaba la **extensión del nombre de archivo enviado por el
  cliente** (`Path(file.filename).suffix`). Un `foto.php` aterrizaba con esa extensión en
  `/static`. El helper compartido `app/core/uploads.py` la deriva del `content-type`
  validado, y además decodifica la imagen con Pillow para probar que lo es.
- El helper también borra el archivo que reemplaza, evitando huérfanos en disco.

## Fuentes que lo mencionan
- [[fuentes/sesion-avatar-pyjwt-y-test-db]] — implementación, PyJWT y aislamiento de tests
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — bug de la cookie, recorte y endurecimiento

## Perspectivas/decisiones
Los avatares se sirven como estáticos públicos (no requieren token): son de bajo riesgo y
así el `<img>` del navegador los carga directo. El upload sí exige autenticación. La ruta
lleva un sufijo aleatorio para evitar colisiones y cacheo obsoleto.

## Contradicciones detectadas
El endpoint vive en `/auth/me/avatar` (perfil propio), coherente con el resto de `/auth/me`.
La descripción original de este documento decía que el guardado usaba `.ext` del archivo
subido: **ya no es cierto** desde el helper compartido.
