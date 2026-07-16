# Arquitectura del Sistema

## Visión General

PastryStock Manager sigue una **Arquitectura Limpia** con separación estricta por capas.
La dependencia fluye siempre hacia adentro: `api → application → domain ← infrastructure`.

```
┌──────────────────────────────────────────────────────┐
│                  Next.js (Frontend)                   │
│         App Router + TypeScript + Tailwind            │
└──────────────────────┬───────────────────────────────┘
                       │ HTTP/JSON
┌──────────────────────▼───────────────────────────────┐
│               FastAPI (Backend)                       │
│  ┌─────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │   API   │→ │ Application │→ │     Domain       │  │
│  │ Routers │  │  Services   │  │ Entities, Enums  │  │
│  │ RBAC MW │  │  Schemas    │  │ Exceptions, VOs  │  │
│  └─────────┘  └──────┬──────┘  └──────────────────┘  │
│                      │ (via interfaces/Protocols)      │
│  ┌───────────────────▼──────────────────────────────┐ │
│  │             Infrastructure                        │ │
│  │  PostgreSQL (ORM)  │  Redis (Cache/PubSub)        │ │
│  └───────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

## Principios SOLID Aplicados

### S — Single Responsibility
Cada módulo tiene una sola razón para cambiar:
- `category_service.py` orquesta la lógica de categorías
- `alert_service.py` maneja exclusivamente las alertas Redis
- Los modelos ORM no contienen lógica de negocio

### O — Open/Closed
- Nuevas categorías se crean sin modificar código (diseño del producto)
- `ALLOWED_MOVEMENTS_BY_ROLE` permite extender roles sin modificar servicios
- Los manejadores de errores mapean excepciones sin tocar los endpoints

### L — Liskov Substitution
- Los repositorios concretos son sustituibles por mocks en pruebas
- Cualquier implementación de `ICategoryRepository` funciona en `CategoryService`

### I — Interface Segregation
- `ISupplyRepository` solo expone métodos que los servicios necesitan
- Los clientes no dependen de métodos que no usan (ej: STAFF no ve endpoints de ENTRY)

### D — Dependency Inversion
- Los servicios dependen de `Protocol` (abstracción), no de clases concretas
- FastAPI inyecta las implementaciones concretas vía `Depends()`

## Flujo de Caché (Redis)

```
GET /api/v1/categories
        │
        ▼
 ¿Existe "categories:active:all" en Redis?
        │
    SÍ ──────────────────────────────► Retornar desde Redis (< 1ms)
        │
    NO  ─────► Consultar PostgreSQL
                      │
                      ▼
              Serializar resultado
                      │
                      ▼
        SET "categories:active:all" TTL=3600s en Redis
                      │
                      ▼
              Retornar al cliente
```

## Flujo de Alertas de Stock

```
POST /api/v1/movements  (EXIT)
        │
        ▼
   SupplyService.register_consumption()
        │
        ├── Validar stock suficiente (dominio puro)
        ├── Actualizar current_stock en PostgreSQL (transacción atómica)
        ├── Insertar movement_history con alert_triggered
        │
        └── ¿stock_after < minimum_stock?
                │
               SÍ ──► AlertService.publish_low_stock()
                              │
                              ▼
                     Redis PUBLISH "alerts:low_stock"
                              │
                              ▼
                    {id, name, current, minimum, deficit}
```

## RBAC por Capas

| Capa | Mecanismo |
|---|---|
| API Router | `Depends(require_roles([UserRole.ADMIN]))` |
| Servicio | `ALLOWED_MOVEMENTS_BY_ROLE[user.role]` |
| Base de Datos | FK `ondelete=RESTRICT` + constraints |
