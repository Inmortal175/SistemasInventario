import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
_redis_pool: Redis | None = None


def _build_pool() -> Redis:
    return aioredis.from_url(
        _settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
        retry_on_timeout=True,
        health_check_interval=30,
    )


async def get_redis() -> Redis:
    """Retorna el cliente Redis singleton. Inicializa el pool si es la primera llamada."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = _build_pool()
    return _redis_pool


async def close_redis() -> None:
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


# ── Helpers con circuit-breaker suave ────────────────────────────────────────
# Si Redis no está disponible, las operaciones retornan None/False
# en lugar de propagar la excepción y romper el flujo de negocio.

async def cache_get(redis: Redis, key: str) -> Any | None:
    try:
        raw = await redis.get(key)
        return json.loads(raw) if raw else None
    except RedisError as exc:
        logger.warning("REDIS_UNAVAILABLE cache_get key=%s err=%s", key, exc)
        return None


async def cache_set(redis: Redis, key: str, value: Any, ttl: int | None = None) -> bool:
    try:
        ttl = ttl or _settings.redis_cache_ttl
        await redis.set(key, json.dumps(value, default=str), ex=ttl)
        return True
    except RedisError as exc:
        logger.warning("REDIS_UNAVAILABLE cache_set key=%s err=%s", key, exc)
        return False


async def cache_delete(redis: Redis, *keys: str) -> bool:
    try:
        await redis.delete(*keys)
        return True
    except RedisError as exc:
        logger.warning("REDIS_UNAVAILABLE cache_delete keys=%s err=%s", keys, exc)
        return False


async def cache_publish(redis: Redis, channel: str, payload: dict[str, Any]) -> bool:
    """Publica un evento en un canal Pub/Sub de Redis."""
    try:
        await redis.publish(channel, json.dumps(payload, default=str))
        return True
    except RedisError as exc:
        logger.warning("REDIS_UNAVAILABLE publish channel=%s err=%s", channel, exc)
        return False


@asynccontextmanager
async def acquire_lock(
    redis: Redis,
    lock_key: str,
    timeout_seconds: int = 5,
) -> AsyncGenerator[bool, None]:
    """Lock pesimista para operaciones críticas de stock (SET NX EX)."""
    acquired = False
    try:
        acquired = await redis.set(lock_key, "1", nx=True, ex=timeout_seconds) or False
        yield acquired
    except RedisError as exc:
        logger.warning("REDIS_UNAVAILABLE acquire_lock key=%s err=%s", lock_key, exc)
        yield True  # degraded mode: proceder sin lock
    finally:
        if acquired:
            await cache_delete(redis, lock_key)
