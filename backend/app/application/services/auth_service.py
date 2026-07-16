import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.application.schemas.auth_schema import LoginRequest, TokenResponse
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.exceptions import InvalidCredentialsError, RateLimitExceededError
from app.infrastructure.cache.cache_keys import login_block_key, login_rate_limit_key
from app.infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository, redis: Redis | None = None) -> None:
        self._repo = user_repo
        self._redis = redis
        self._settings = get_settings()

    async def login(self, data: LoginRequest, client_ip: str | None = None) -> TokenResponse:
        # ── HU-04-02: si la IP está bloqueada, rechazar antes de tocar la BD ──
        if client_ip:
            await self._raise_if_blocked(client_ip)

        user = await self._repo.get_by_email(data.username)  # username = email en OAuth2
        if user is None or not user.is_active or not verify_password(
            data.password, user.hashed_password
        ):
            if client_ip:
                await self._register_failed_attempt(client_ip)
            raise InvalidCredentialsError()

        # Login correcto → limpiar el contador de intentos de esa IP
        if client_ip:
            await self._reset_attempts(client_ip)

        token = create_access_token(user_id=user.id, role=user.role.value)
        return TokenResponse(
            access_token=token,
            expires_in=self._settings.access_token_expire_minutes,
            user_id=user.id,
            full_name=user.full_name,
            role=user.role,
            avatar_url=user.avatar_url,
        )

    async def _raise_if_blocked(self, ip: str) -> None:
        if self._redis is None:
            return
        try:
            ttl = await self._redis.ttl(login_block_key(ip))
        except RedisError as exc:
            logger.warning("REDIS_UNAVAILABLE rate_limit_check err=%s", exc)
            return
        if ttl and ttl > 0:
            raise RateLimitExceededError(retry_after_seconds=int(ttl))

    async def _register_failed_attempt(self, ip: str) -> None:
        if self._redis is None:
            return
        try:
            key = login_rate_limit_key(ip)
            attempts = await self._redis.incr(key)
            if attempts == 1:
                # Primer fallo del ciclo: fija la ventana deslizante de 15 min.
                await self._redis.expire(key, self._settings.login_window_seconds)
            if attempts >= self._settings.login_max_attempts:
                await self._redis.set(
                    login_block_key(ip), "1", ex=self._settings.login_block_seconds
                )
                logger.warning("LOGIN_IP_BLOCKED ip=%s attempts=%s", ip, attempts)
        except RedisError as exc:
            logger.warning("REDIS_UNAVAILABLE rate_limit_incr err=%s", exc)

    async def _reset_attempts(self, ip: str) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.delete(login_rate_limit_key(ip), login_block_key(ip))
        except RedisError as exc:
            logger.warning("REDIS_UNAVAILABLE rate_limit_reset err=%s", exc)

    async def create_initial_superadmin(self, email: str, password: str) -> None:
        """Seed del superadministrador en el primer arranque."""
        existing = await self._repo.get_by_email(email)
        if existing:
            return
        from app.domain.enums import UserRole
        await self._repo.create(
            email=email,
            full_name="Super Administrador",
            hashed_password=hash_password(password),
            role=UserRole.SUPERADMIN,
            is_active=True,
        )
