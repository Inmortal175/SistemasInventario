"""Restablece la contraseña de un usuario desde el servidor (CLI).

Medio de recuperación para el caso en que NADIE con acceso pueda restablecer la
clave por la API — típicamente el propio SUPERADMIN bootstrap. Equivale al comando
`changepassword` de frameworks como Django.

Uso:
    docker-compose exec backend python scripts/reset_password.py \
        --email superadmin@mipasteleria.pe --password "NuevaClave@2026"

Si se omite --password, se genera una temporal segura y se imprime una sola vez.
"""

from __future__ import annotations

import argparse
import asyncio
import secrets
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password  # noqa: E402
from app.infrastructure.database.connection import AsyncSessionLocal, engine  # noqa: E402
from app.infrastructure.repositories.user_repository import UserRepository  # noqa: E402


def _generate_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + "@#$%*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restablece la contraseña de un usuario.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", default=None, help="Si se omite, se genera una temporal")
    return parser.parse_args()


async def reset(email: str, password: str | None) -> int:
    new_password = password or _generate_password()
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_email(email)
        if user is None:
            print(f"✗ No existe un usuario con email '{email}'.")
            return 1
        await repo.set_password(user.id, hash_password(new_password))
        await session.commit()

    print(f"✅ Contraseña restablecida para '{email}' (rol {user.role.value}).")
    if password is None:
        print(f"   Contraseña temporal (cámbiala tras ingresar): {new_password}")
    return 0


async def main() -> int:
    args = _parse_args()
    try:
        return await reset(args.email, args.password)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
