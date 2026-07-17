---
title: "Campo de contraseña con visibilidad"
tags: [ux, accesibilidad, react, formularios, contrasenas]
source_count: 1
---

# Campo de contraseña con visibilidad

## Definición
Un `<input type="password">` oculta lo que se escribe, lo que provoca errores de tecleo
invisibles — sobre todo en móvil y con contraseñas largas. El botón de revelar (el "ojito")
es hoy el estándar de facto, y el NIST lo recomienda explícitamente: enmascarar siempre
perjudica la usabilidad más de lo que protege.

## Fuentes que lo mencionan
- [[fuentes/sesion-despliegue-railway-csrf-y-contrasenas]] — implementación del componente

## Decisión de diseño
Un único `PasswordInput` en `components/`, no la lógica repetida en cada formulario. Había
seis campos en cuatro ficheros: login, alta de usuario, reset por admin y los tres del
cambio de contraseña.

```tsx
type PasswordInputProps = Omit<ComponentPropsWithoutRef<"input">, "type">;
```

Al aceptar las props nativas de `<input>` y solo prohibir `type`, sustituye al input
original sin cambiar nada más del formulario — el `className`, `required`, `minLength` y
`placeholder` siguen funcionando igual.

## Perspectivas/decisiones

- **`type` alternado, no un CSS truco.** `visible ? "text" : "password"`. Simple y respeta
  los gestores de contraseñas.
- **Accesibilidad**: `aria-label` que cambia con el estado ("Mostrar"/"Ocultar contraseña")
  y `aria-pressed` para que el lector de pantalla anuncie el toggle. El botón queda en el
  orden de tabulación: un usuario de teclado también necesita poder revelar.
- **`type="button"` es obligatorio.** Sin él, un `<button>` dentro de un `<form>` envía el
  formulario al pulsarlo — el bug clásico de este componente.
- **`autoComplete` explícito** en cada uso: `current-password` en login y en la contraseña
  actual; `new-password` en altas, resets y contraseñas nuevas. Sin esto, los gestores
  ofrecen la sugerencia equivocada.
- **El padding se apila**: `.input` vive en `@layer components`, así que la utilidad `pr-10`
  la sobreescribe sin conflicto y el texto no pasa por debajo del icono.
- Iconos `eye`/`eyeSlash` añadidos al registro central de
  [[conceptos/iconos-fontawesome-nextjs]], no importados sueltos.

## Contradicciones detectadas
Ninguna.
