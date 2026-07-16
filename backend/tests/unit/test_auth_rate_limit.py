"""HU-04-02: rate limiting de login por IP con Redis."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.schemas.auth_schema import LoginRequest
from app.application.services.auth_service import AuthService
from app.domain.enums import UserRole
from app.domain.exceptions import InvalidCredentialsError, RateLimitExceededError


@pytest.mark.asyncio
async def test_blocked_ip_is_rejected_before_db(mock_redis):
    """IP bloqueada (TTL>0) → RateLimitExceededError sin consultar la BD."""
    mock_redis.ttl = AsyncMock(return_value=600)
    user_repo = AsyncMock()

    service = AuthService(user_repo=user_repo, redis=mock_redis)
    with pytest.raises(RateLimitExceededError) as exc:
        await service.login(
            LoginRequest(username="x@y.com", password="bad"), client_ip="1.2.3.4"
        )
    assert exc.value.retry_after_seconds == 600
    user_repo.get_by_email.assert_not_awaited()


@pytest.mark.asyncio
async def test_fifth_failed_attempt_blocks_ip(mock_redis):
    """Al alcanzar 5 intentos, se fija la clave de bloqueo con TTL."""
    mock_redis.ttl = AsyncMock(return_value=-2)      # no bloqueada aún
    mock_redis.incr = AsyncMock(return_value=5)      # este es el 5º fallo
    user_repo = AsyncMock()
    user_repo.get_by_email = AsyncMock(return_value=None)  # credenciales inválidas

    service = AuthService(user_repo=user_repo, redis=mock_redis)
    with pytest.raises(InvalidCredentialsError):
        await service.login(
            LoginRequest(username="x@y.com", password="bad"), client_ip="9.9.9.9"
        )
    # Se registró el bloqueo (set con expiración)
    assert mock_redis.set.await_count >= 1


@pytest.mark.asyncio
async def test_successful_login_resets_attempts(mock_redis):
    """Login correcto limpia el contador de intentos de la IP."""
    mock_redis.ttl = AsyncMock(return_value=-2)
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_active = True
    user.full_name = "Pastelero"
    user.role = UserRole.STAFF
    user.avatar_url = None
    user.hashed_password = "$2b$12$abcdefghijklmnopqrstuv"  # no se verifica aquí

    user_repo = AsyncMock()
    user_repo.get_by_email = AsyncMock(return_value=user)

    # Forzamos verify_password=True monkeypatcheando el módulo de servicio
    import app.application.services.auth_service as mod
    original = mod.verify_password
    mod.verify_password = lambda plain, hashed: True
    try:
        service = AuthService(user_repo=user_repo, redis=mock_redis)
        token = await service.login(
            LoginRequest(username="pastelero@x.com", password="ok"), client_ip="5.5.5.5"
        )
    finally:
        mod.verify_password = original

    assert token.access_token
    mock_redis.delete.assert_awaited()   # reset de intentos
