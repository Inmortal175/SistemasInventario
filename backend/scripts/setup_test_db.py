"""Crea y migra la base de datos de tests `pastry_test` (idempotente).

Aísla las pruebas de integración de la BD de desarrollo: la suite TRUNCA tablas,
así que jamás debe correr contra `pastry_inventory`. Este script:
  1. Crea la base `pastry_test` si no existe.
  2. Crea los ENUMs de dominio (equivalente a sql/init.sql).
  3. Aplica todas las migraciones de Alembic sobre ella.

Uso (una sola vez, o tras añadir migraciones):
    docker-compose exec backend python scripts/setup_test_db.py
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg  # noqa: E402

from app.core.config import get_settings  # noqa: E402

_TEST_DB = "pastry_test"


def _dsn(url: str) -> str:
    # asyncpg no entiende el prefijo +asyncpg de SQLAlchemy.
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def _ensure_database() -> tuple[str, str]:
    settings = get_settings()
    admin_url, _sep, dev_db = settings.database_url.rpartition("/")
    test_async = f"{admin_url}/{_TEST_DB}"

    # Conectarse a la BD de desarrollo para poder emitir CREATE DATABASE.
    conn = await asyncpg.connect(_dsn(f"{admin_url}/{dev_db}"))
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", _TEST_DB
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{_TEST_DB}"')
            print(f"✅ Base de datos '{_TEST_DB}' creada.")
        else:
            print(f"✓ La base '{_TEST_DB}' ya existe.")
    finally:
        await conn.close()

    return test_async, _dsn(test_async)


async def _create_enums(test_dsn: str) -> None:
    init_sql = (Path(__file__).resolve().parent.parent / "sql" / "init.sql").read_text(
        encoding="utf-8"
    )
    conn = await asyncpg.connect(test_dsn)
    try:
        await conn.execute(init_sql)
        print("✓ ENUMs de dominio asegurados en la base de tests.")
    finally:
        await conn.close()


def _run_migrations(test_async_url: str) -> None:
    # Alembic lee DATABASE_URL vía get_settings(); lo apuntamos a la base de tests.
    import os

    env = {**os.environ, "DATABASE_URL": test_async_url}
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(Path(__file__).resolve().parent.parent),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit("✗ Falló la migración de la base de tests.")
    print("✓ Migraciones aplicadas en la base de tests.")


async def main() -> int:
    test_async, test_dsn = await _ensure_database()
    await _create_enums(test_dsn)
    _run_migrations(test_async)
    print("\n✅ Base de tests lista. Ya puedes correr `pytest` sin tocar la BD de desarrollo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
