---
title: "Configuración del sistema en base de datos"
tags: [ajustes, configuracion, branding, singleton, redis, arquitectura]
source_count: 1
---

# Configuración del sistema en base de datos

## Definición
Tabla `system_settings` de **fila única** que guarda la identidad visual y las reglas de
negocio de la instalación, editables en caliente desde `/settings` (solo SUPERADMIN), sin
reiniciar el contenedor. Se opone a la configuración por variables de entorno, reservada
para lo que es del despliegue.

## Implementación
- **Modelo**: `SystemSettingsModel`, PK entera con `CheckConstraint("id = 1")`. La fila
  única hace imposible insertar una segunda configuración, así que ninguna lectura necesita
  desempatar. `SettingsRepository.get()` la crea perezosamente si falta.
- **Migraciones**: `004_system_settings` (app_name, logo_url, theme) → `005_login_backgrounds`
  (3 fondos) → `006_settings_business_rules` (velo, expiration_alert_days, currency_code,
  locale, page_size, business_name, tax_id, address, phone) con CHECKs de rango.
- **Caché**: clave Redis `settings:system`, invalidada en cada escritura. El layout raíz la
  lee en cada render, de ahí la caché.
- **API**: `GET /api/v1/settings` **sin autenticación** (el login necesita nombre, logo y
  tema antes de que exista sesión); `PATCH`, `POST/DELETE /logo`,
  `POST/DELETE /login-background/{device}` exigen SUPERADMIN.
- **Semántica del PATCH**: `None` = «no tocar este campo»; cadena vacía `""` = «borrar»
  (solo en los campos de texto libre). El servicio separa unos de otros y usa
  `SettingsRepository.clear()` para los vaciados.

## La frontera: negocio vs. despliegue
| Va a la base de datos | Se queda en el entorno |
|---|---|
| `expiration_alert_days` | `login_max_attempts` |
| `currency_code`, `locale` | `login_block_seconds` |
| `page_size` | `access_token_expire_minutes` |
| nombre, logo, tema, fondos | `secret_key`, `database_url` |

El criterio: si quien conoce la respuesta es el dueño de la pastelería, va a la base. Si es
quien despliega, va al entorno. Exponer el rate limiting en la interfaz permitiría desactivar
la protección contra fuerza bruta con un clic, sin entender las consecuencias.

## Una sola fuente de verdad
`config.app_name` (entorno) y `system_settings.app_name` (base) competían: la interfaz decía
un nombre y `/docs` otro. Ganó la base de datos. `apply_app_name()` en `main.py` fija
`app.title` y anula `app.openapi_schema` — se ejecuta al arrancar (leyendo de la BD) y en el
endpoint `PATCH /settings`. Con varios workers, cada proceso se entera al arrancar o al
atender ese PATCH.

## Fuentes que lo mencionan
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — diseño e implementación completa

## Perspectivas/decisiones
Se descartó guardar el tema como preferencia por usuario: la identidad visual de una
pastelería es una sola, y el mismo formulario que cambia el nombre y el logo debe cambiar
la paleta. Ver [[conceptos/temas-css-variables-tailwind]].

## Contradicciones detectadas
Ninguna. Relacionado con [[conceptos/cache-obsoleta-tras-cambio-de-schema]]: añadir campos a
esta tabla exige que el servicio tolere entradas de caché con la forma anterior.
