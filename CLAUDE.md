# PastryStock Manager — Contexto para Claude Code

## Descripción del proyecto
MVP de sistema de gestión de inventario para pastelerías. Maneja insumos perecederos,
herramientas de cocina y útiles de limpieza con control RBAC, categorización dinámica
con caché Redis, ubicaciones físicas rotuladas y auditoría inmutable.

## Metodología
- **SDD** (Spec-Driven Development): historias en BDD/Gherkin en `docs/user-stories.md`
- **TDD**: pruebas unitarias primero, luego integración. Suite en `backend/tests/`
- **SOLID**: arquitectura limpia por capas en `backend/app/`

## Stack obligatorio
- Backend: FastAPI + SQLAlchemy 2.0 async + asyncpg
- Frontend: Next.js 15 App Router + TypeScript + Tailwind CSS
- BD: PostgreSQL 16
- Caché: Redis 7
- Despliegue: Docker Compose

## Estructura de capas del backend
```
domain/        → Entidades, enums, excepciones, value objects (sin dependencias externas)
infrastructure/ → ORM models, repositorios concretos, cliente Redis
application/   → Servicios de casos de uso, schemas Pydantic
api/           → Routers FastAPI, middlewares RBAC
core/          → Config (pydantic-settings), security (JWT)
```

## Reglas de negocio críticas
1. `LocationCode` sigue el patrón `^(EST|REF|FRZ|CAB|CON|ALM)-\d{2}(-F\d{1,2})?$`
   Solo EST admite sufijo de fila (-FX).
2. `movement_history` es INMUTABLE: sin `updated_at`, FK con `ondelete=RESTRICT`.
3. Stock nunca puede ser negativo: constraint en DB + validación en `SupplyService`.
4. STAFF solo puede registrar `EXIT` y `WASTE`. `ENTRY` y ajustes son solo ADMIN+.
5. Creación de categorías: Redis se consulta primero (cache-first), PostgreSQL como fallback.

## ENUMs de dominio
Definidos en `backend/sql/init.sql` (ejecutado en primer boot de PostgreSQL) y
referenciados en SQLAlchemy con `create_type=False` para evitar duplicados.

## Variables de entorno
Ver `.env.example`. Las principales: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`.

## Comandos frecuentes
```bash
docker-compose up -d                          # levantar entorno
docker-compose exec backend alembic upgrade head  # aplicar migraciones
docker-compose exec backend pytest -v         # correr tests
docker-compose logs -f backend                # ver logs del backend
```

## Convenciones de código
- Sin comentarios obvios. Solo comentar el PORQUÉ cuando no es evidente.
- Excepciones de dominio en `domain/exceptions.py`, nunca HTTPException directa en servicios.
- Los servicios reciben interfaces (Protocol), no implementaciones concretas (DIP).
- `async/await` en toda la capa de acceso a datos.
