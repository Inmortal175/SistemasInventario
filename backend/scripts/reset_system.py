"""Reset del sistema: borra todos los datos de negocio y deja solo a los admins.

Pensado para dejar la base limpia antes de un `seed_demo.py` nuevo (demos, QA).
Borra insumos, lotes, categorías, ubicaciones, recetas, producción y el historial
de movimientos, y purga las cachés de Redis (que son cache-first: si no se limpian,
la app sigue sirviendo listas vacías/viejas aunque la DB ya tenga datos nuevos).

Conserva:
  - Usuarios ADMIN y SUPERADMIN (los de rol STAFF se eliminan).
  - `system_settings` (identidad visual y configuración del sistema).

Es DESTRUCTIVO e irreversible. Exige `--yes` para ejecutarse de verdad; sin ese
flag hace un dry-run que solo reporta qué borraría.

Uso:
    python scripts/reset_system.py            # dry-run: solo muestra conteos
    python scripts/reset_system.py --yes      # ejecuta el borrado
    python scripts/reset_system.py --yes --keep-staff   # conserva también STAFF
    python scripts/reset_system.py --yes --keep-cache   # no toca Redis
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select, text  # noqa: E402

from app.domain.enums import UserRole  # noqa: E402
from app.infrastructure.cache.redis_client import close_redis, get_redis  # noqa: E402
from app.infrastructure.database.connection import AsyncSessionLocal, engine  # noqa: E402
from app.infrastructure.database.models.user_model import UserModel  # noqa: E402

# Tablas de datos de negocio, de hija a padre. TRUNCATE ... CASCADE resuelve el
# orden de las dependencias entre ellas; se listan todas para no depender del
# cascade y dejar explícito el alcance del borrado. `users` y `system_settings`
# NO están aquí a propósito: son referenciadas, no se truncan.
BUSINESS_TABLES = [
    "production_run_items",
    "production_runs",
    "movement_history",
    "recipe_items",
    "recipes",
    "supply_batches",
    "supply_items",
    "locations",
    "dynamic_categories",
]

# Patrones/llaves de Redis que la app sirve cache-first. Un reset que no las
# limpie deja al frontend mostrando lo viejo. Ver app/infrastructure/cache/cache_keys.py
CACHE_PATTERNS = [
    "categories:*",
    "category:*",
    "supplies:page:*",
    "dashboard:kpis",
    "settings:system",
]


async def _counts(session) -> dict[str, int]:
    out: dict[str, int] = {}
    for table in BUSINESS_TABLES:
        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        out[table] = result.scalar_one()
    return out


async def _purge_redis() -> int:
    """Borra las llaves cache-first de la app. No usa FLUSHDB para no tumbar
    rate-limits de login ni blacklists de tokens que no son datos de demo."""
    redis = await get_redis()
    deleted = 0
    for pattern in CACHE_PATTERNS:
        if "*" in pattern:
            keys = [key async for key in redis.scan_iter(match=pattern, count=500)]
            if keys:
                deleted += await redis.delete(*keys)
        else:
            deleted += await redis.delete(pattern)
    return deleted


async def reset(*, execute: bool, keep_staff: bool, purge_cache: bool) -> int:
    async with AsyncSessionLocal() as session:
        before = await _counts(session)

        admins_stmt = select(func.count()).select_from(UserModel).where(
            UserModel.role.in_([UserRole.SUPERADMIN, UserRole.ADMIN])
        )
        staff_stmt = select(func.count()).select_from(UserModel).where(
            UserModel.role == UserRole.STAFF
        )
        admins = (await session.execute(admins_stmt)).scalar_one()
        staff = (await session.execute(staff_stmt)).scalar_one()

        print("── Estado actual ─────────────────────────────")
        for table, count in before.items():
            print(f"   {table:<22} {count:>6}")
        print(f"   {'usuarios admin':<22} {admins:>6}  (se conservan)")
        print(f"   {'usuarios staff':<22} {staff:>6}  "
              f"({'se conservan' if keep_staff else 'se ELIMINAN'})")

        if not execute:
            print("\n⚠  DRY-RUN: nada se borró. Vuelve a correr con --yes para ejecutar.")
            return 0

        if admins == 0:
            raise SystemExit(
                "✗ No hay ningún usuario ADMIN/SUPERADMIN: abortando para no dejar "
                "el sistema sin acceso. Corre scripts/seed_admin.py primero."
            )

        await session.execute(
            text(f"TRUNCATE {', '.join(BUSINESS_TABLES)} RESTART IDENTITY CASCADE")
        )

        deleted_users = 0
        if not keep_staff:
            result = await session.execute(
                text("DELETE FROM users WHERE role = 'STAFF'")
            )
            deleted_users = result.rowcount or 0

        await session.commit()

    cache_deleted = 0
    if purge_cache:
        cache_deleted = await _purge_redis()

    print("\n✅ Reset completo.")
    print(f"   datos de negocio: borrados ({sum(before.values())} filas)")
    print(f"   usuarios STAFF:   {deleted_users} eliminados")
    print(f"   llaves de caché:  {cache_deleted} borradas de Redis")
    print("   admins y system_settings: intactos")
    print("\n➡  Ahora corre:  python scripts/seed_demo.py")
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description="Resetea el sistema conservando admins.")
    parser.add_argument("--yes", action="store_true", help="Ejecuta el borrado (sin esto es dry-run).")
    parser.add_argument("--keep-staff", action="store_true", help="Conserva también usuarios STAFF.")
    parser.add_argument("--keep-cache", action="store_true", help="No purga Redis.")
    args = parser.parse_args()
    try:
        return await reset(
            execute=args.yes,
            keep_staff=args.keep_staff,
            purge_cache=not args.keep_cache,
        )
    finally:
        await close_redis()
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
