---
title: "Caché obsoleta tras un cambio de schema"
tags: [redis, cache, migraciones, pydantic, resiliencia, despliegue]
source_count: 1
---

# Caché obsoleta tras un cambio de schema

## Definición
Cuando un objeto cacheado en Redis se serializa con una versión del schema y se deserializa
con otra que añadió campos obligatorios, la validación falla y el endpoint devuelve 500.
Ocurre en **cada despliegue** que amplíe un modelo cacheado.

## Cómo se manifestó
Tras aplicar la migración `005` (tres columnas nuevas en `system_settings`),
`GET /api/v1/settings` respondía **500**:

```
pydantic_core.ValidationError: 3 validation errors for SettingsResponse
... For further information visit https://errors.pydantic.dev/2.10/v/missing
```

La base ya tenía las columnas; Redis seguía con la forma anterior del objeto.

## Solución: que la caché no pueda tumbar la API
```python
cached = await cache_get(self._redis, SYSTEM_SETTINGS_KEY)
if cached is not None:
    try:
        return SettingsResponse(**cached)
    except ValidationError:
        # Entrada escrita por una versión anterior del schema: tras un deploy
        # que agrega campos, la caché vieja no debe tumbar la API.
        logger.warning("SETTINGS_CACHE_STALE key=%s", SYSTEM_SETTINGS_KEY)
        await cache_delete(self._redis, SYSTEM_SETTINGS_KEY)

settings = await self._repo.get()   # PostgreSQL es la fuente de verdad
```

La entrada corrupta se descarta, se registra y se reconstruye desde PostgreSQL. Se verificó
sin limpiar la clave a mano: la primera petición ya respondió 200 y dejó el warning.

## Regla general
**Toda entrada de caché es una promesa de un contrato pasado.** Un `cache_get` que alimenta
directamente un constructor de Pydantic debe asumir que la forma pudo cambiar. Alternativas:
versionar la clave (`settings:system:v2`), purgar en el despliegue, o —lo aplicado aquí—
tolerar el fallo y reconstruir.

## Fuentes que lo mencionan
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — detectado al migrar 004 → 005

## Perspectivas/decisiones
Se prefirió la tolerancia en el código a purgar Redis en el despliegue: no depende de que
alguien recuerde un paso manual, y el coste es un miss puntual por cada worker.

Aplica a las otras cachés del proyecto ([[conceptos/cache-first-paginacion]]:
`supplies:page:*`, `categories:active:all`, `dashboard:kpis`), que hoy **no** tienen esta
protección. Riesgo abierto.

## Contradicciones detectadas
Ninguna. Se relaciona con [[conceptos/configuracion-sistema-en-bd]], la tabla que provocó
el caso.
