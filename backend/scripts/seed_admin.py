"""Seed del usuario administrador inicial (bootstrap).

Crea el primer usuario con privilegios (SUPERADMIN por defecto) a partir de las
variables `SUPERADMIN_EMAIL` / `SUPERADMIN_PASSWORD` definidas en la config.
Desde esa cuenta se pueden crear luego los ADMIN y STAFF vía la API.

Es idempotente: si el correo ya existe, no lo duplica; solo reactiva la cuenta
si estaba desactivada.

Uso:
    docker-compose exec backend python scripts/seed_admin.py
    docker-compose exec backend python scripts/seed_admin.py \
        --email jefe@pasteleria.com --password "Secreto@123" --role ADMIN
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Permite `python scripts/seed_admin.py` desde cualquier cwd: agrega la raíz
# del backend (que contiene el paquete `app`) al path de importación.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.domain.enums import UserRole  # noqa: E402
from app.infrastructure.database.connection import AsyncSessionLocal, engine  # noqa: E402
from app.infrastructure.repositories.user_repository import UserRepository  # noqa: E402


def _parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Crea el usuario administrador inicial.")
    parser.add_argument("--email", default=settings.superadmin_email)
    parser.add_argument("--password", default=settings.superadmin_password)
    parser.add_argument("--name", default="Administrador")
    parser.add_argument(
        "--role",
        default=UserRole.SUPERADMIN.value,
        choices=[r.value for r in UserRole],
    )
    return parser.parse_args()


async def seed(email: str, password: str, name: str, role: UserRole) -> int:
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)

        existing = await repo.get_by_email(email)
        if existing is not None:
            if not existing.is_active:
                existing.is_active = True
                await session.commit()
                print(f"↺ Usuario '{email}' reactivado.")
                return 0
            print(f"✓ El usuario '{email}' ya existe ({existing.role.value}). Nada que hacer.")
            return 0

        user = await repo.create(
            email=email,
            full_name=name,
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
        )
        await session.commit()
        print(
            f"✅ {role.value} creado:\n"
            f"   id:     {user.id}\n"
            f"   email:  {user.email}\n"
            f"   nombre: {user.full_name}"
        )
        return 0


async def main() -> int:
    args = _parse_args()
    try:
        return await seed(
            email=args.email,
            password=args.password,
            name=args.name,
            role=UserRole(args.role),
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
