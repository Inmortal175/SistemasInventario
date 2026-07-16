# PastryStock Manager

Sistema de Gestión de Inventario Inteligente y Dinámico para Pastelerías.

Controla insumos perecederos, herramientas y útiles de limpieza con trazabilidad completa:
lotes con vencimiento y consumo **FIFO**, recetas (BOM) que descuentan ingredientes de forma
atómica al producir, producto terminado como inventario, valorización financiera, alertas en
tiempo real por WebSocket, auditoría inmutable y control de acceso por roles.

Desarrollado con **SDD** (Spec-Driven Development) y **TDD**: la especificación precede al código.
La evidencia completa del ciclo de vida está en [`docs/spec/`](docs/spec/).

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI 0.115 + SQLAlchemy 2.0 (async) + asyncpg |
| Frontend | Next.js 15 (App Router, TypeScript, Tailwind CSS) |
| Base de datos | PostgreSQL 16 |
| Caché / Mensajería | Redis 7 (caché, Pub/Sub, blacklist JWT, rate limit) |
| Despliegue local | Docker + Docker Compose |
| Despliegue productivo | Railway (4 servicios) |

## Levantar entorno

```bash
# 1. Copiar variables de entorno
cp .env.example .env
```

> ⚠️ Edita el `.env`: los valores `REEMPLAZAR_*` son marcadores, no valores válidos.
> Genera `SECRET_KEY` y `NEXTAUTH_SECRET` con `openssl rand -hex 32` y define una
> `SUPERADMIN_PASSWORD` propia.

```bash
# 2. Levantar los 4 servicios
docker-compose up -d

# 3. Verificar que los contenedores están sanos
docker-compose ps

# 4. Aplicar migraciones (primer arranque)
docker-compose exec backend alembic upgrade head

# 5. Crear el usuario superadministrador (sin esto no puedes iniciar sesión)
docker-compose exec backend python scripts/seed_admin.py

# 6. (Opcional) Sembrar datos de demostración
docker-compose exec backend python scripts/seed_demo.py
```

Los servicios estarán disponibles en:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Docs interactivas (OpenAPI):** http://localhost:8000/docs

Inicia sesión con las credenciales que definiste en `SUPERADMIN_EMAIL` / `SUPERADMIN_PASSWORD`.
Ambos seeds son idempotentes: puedes volver a ejecutarlos sin duplicar datos.

## Ejecutar pruebas

```bash
docker-compose exec backend pytest -v
```

La suite corre contra una base de datos aislada (`pastry_test`), separada de la de desarrollo.
Si es la primera vez:

```bash
docker-compose exec backend python scripts/setup_test_db.py
```

## Desplegar en producción

Guía paso a paso para Railway (PostgreSQL + Redis + backend + frontend, con auto-deploy desde
GitHub): [`docs/deployment-railway.md`](docs/deployment-railway.md).

## Documentación

### Evidencia SDD — ciclo de vida ([`docs/spec/`](docs/spec/))

| Documento | Fase | Descripción |
|---|---|---|
| [00-constitution.md](docs/spec/00-constitution.md) | Gobernanza | Principios no negociables del proyecto |
| [01-analisis.md](docs/spec/01-analisis.md) | Análisis | Problema, alcance, requisitos y riesgos |
| [02-specification.md](docs/spec/02-specification.md) | Especificación | Índice maestro de las historias de usuario |
| [03-plan.md](docs/spec/03-plan.md) | Diseño | Stack, capas, contrato de API, decisiones técnicas |
| [04-tasks.md](docs/spec/04-tasks.md) | Plan de trabajo | Descomposición en tareas ordenadas y trazables |
| [05-deployment.md](docs/spec/05-deployment.md) | Despliegue | Topología, migraciones y checklist de verificación |
| [06-traceability.md](docs/spec/06-traceability.md) | Cierre | Matriz Requisito → Tarea → Código → Prueba |

### Documentación técnica

| Documento | Descripción |
|---|---|
| [docs/user-stories.md](docs/user-stories.md) | Especificaciones BDD/Gherkin (fuente canónica del spec) |
| [docs/architecture.md](docs/architecture.md) | Arquitectura del sistema y principios SOLID |
| [docs/database-schema.md](docs/database-schema.md) | Modelo relacional y decisiones de diseño |
| [docs/test-matrix.md](docs/test-matrix.md) | Matriz de casos de prueba (SDT) |
| [docs/wiki/](docs/wiki/) | Bitácora de sesiones y conceptos técnicos del desarrollo |
