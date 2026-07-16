import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from redis.exceptions import RedisError

from app.core.security import decode_access_token
from app.domain.enums import UserRole
from app.infrastructure.cache.cache_keys import (
    token_blacklist_key,
    token_valid_from_key,
)
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.database.connection import get_async_session
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={"error_code": "INVALID_CREDENTIALS", "message": "Token inválido o expirado"},
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> UserModel:
    payload = decode_access_token(token)
    if payload is None:
        raise _CREDENTIALS_EXCEPTION

    # HU-10-02: rechazar tokens de usuarios suspendidos (blacklist Redis) y
    # tokens emitidos antes de un restablecimiento de contraseña (época de sesión).
    try:
        if await redis.exists(token_blacklist_key(payload.sub)):
            raise _CREDENTIALS_EXCEPTION
        valid_from = await redis.get(token_valid_from_key(payload.sub))
        if valid_from and payload.iat is not None:
            if payload.iat.timestamp() < float(valid_from):
                raise _CREDENTIALS_EXCEPTION
    except RedisError:
        # Redis caído → confiar en el flag is_active de PostgreSQL (fail-open a BD).
        pass

    repo = UserRepository(session)
    user = await repo.get_by_id(uuid.UUID(payload.sub))
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXCEPTION
    return user


def require_roles(*roles: UserRole):
    """Factory de dependencia que valida el rol del usuario autenticado."""
    async def _checker(
        current_user: Annotated[UserModel, Depends(get_current_user)],
    ) -> UserModel:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Se requiere uno de los roles: {[r.value for r in roles]}",
                },
            )
        return current_user
    return _checker


# Alias tipados para usar con Depends() en endpoints
CurrentUser = Annotated[UserModel, Depends(get_current_user)]
RedisClient = Annotated[Redis, Depends(get_redis)]
DBSession = Annotated[AsyncSession, Depends(get_async_session)]
