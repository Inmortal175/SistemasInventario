# PastryStock Manager

Sistema de Gestión de Inventario Inteligente y Dinámico para Pastelerías.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI 0.115 + SQLAlchemy 2.0 (async) |
| Frontend | Next.js 15 (App Router, TypeScript, Tailwind CSS) |
| Base de datos | PostgreSQL 16 |
| Caché / Mensajería | Redis 7 |
| Despliegue local | Docker + Docker Compose |

## Levantar entorno

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Levantar todos los servicios
docker-compose up -d

# 3. Verificar que los 4 contenedores están corriendo
docker-compose ps
```

Los servicios estarán disponibles en:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Docs interactivas:** http://localhost:8000/docs
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

## Ejecutar migraciones (primera vez)

```bash
docker-compose exec backend alembic upgrade head
```

## Ejecutar pruebas

```bash
docker-compose exec backend pytest -v
```

## Documentación técnica

| Documento | Descripción |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Arquitectura del sistema y principios SOLID |
| [docs/database-schema.md](docs/database-schema.md) | Modelo relacional y decisiones de diseño |
| [docs/user-stories.md](docs/user-stories.md) | Especificaciones BDD/Gherkin (SDD) |
| [docs/test-matrix.md](docs/test-matrix.md) | Matriz de casos de prueba (SDT) |
