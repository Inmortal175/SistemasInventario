"""Fixtures de integración: app real + PostgreSQL + Redis reales.

Se usa NullPool para no retener conexiones asyncpg entre event loops
(cada test corre en su propio loop bajo asyncio_mode=auto). La base se limpia
por TRUNCATE antes de cada test para garantizar aislamiento.
"""
import os
import uuid
from collections.abc import AsyncIterator
from types import SimpleNamespace

import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.domain.enums import UserRole
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.database.connection import get_async_session
from app.infrastructure.database.models.user_model import UserModel
from app.main import app

_settings = get_settings()

# ── Aislamiento de la BD de tests ─────────────────────────────────────────────
# Las pruebas de integración TRUNCAN tablas; jamás deben correr contra la BD de
# desarrollo. Derivamos una base desechable `pastry_test` y un Redis en el índice 1
# a partir de las URLs configuradas. Se pueden sobreescribir con TEST_DATABASE_URL
# / TEST_REDIS_URL. Ver scripts/setup_test_db.py para crearla/migrarla.
def _derive_test_db_url() -> str:
    override = os.getenv("TEST_DATABASE_URL")
    if override:
        return override
    base, _sep, _db = _settings.database_url.rpartition("/")
    return f"{base}/pastry_test"


def _derive_test_redis_url() -> str:
    override = os.getenv("TEST_REDIS_URL")
    if override:
        return override
    base, _sep, _db = _settings.redis_url.rpartition("/")
    return f"{base}/1"


_TEST_DATABASE_URL = _derive_test_db_url()
_TEST_REDIS_URL = _derive_test_redis_url()

# Orden importa: se truncan primero las tablas hijas. CASCADE cubre las FK.
_TABLES = (
    "production_run_items, production_runs, recipe_items, recipes, supply_batches, "
    "movement_history, supply_items, dynamic_categories, locations, users"
)

_DEFAULT_PASSWORD = "Test@1234"


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator:
    engine = create_async_engine(_TEST_DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_sessionmaker(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def test_redis(db_engine) -> AsyncIterator:
    client = aioredis.from_url(_TEST_REDIS_URL, decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(db_engine) -> AsyncIterator[None]:
    async with db_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {_TABLES} RESTART IDENTITY CASCADE"))
    yield


@pytest_asyncio.fixture
async def client(db_sessionmaker, test_redis) -> AsyncIterator[AsyncClient]:
    async def _override_session():
        async with db_sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def _override_redis():
        return test_redis

    app.dependency_overrides[get_async_session] = _override_session
    app.dependency_overrides[get_redis] = _override_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _make_user(db_sessionmaker, role: UserRole) -> UserModel:
    async with db_sessionmaker() as session:
        user = UserModel(
            email=f"{role.value.lower()}-{uuid.uuid4().hex[:8]}@test.local",
            full_name=f"{role.value} Test",
            hashed_password=hash_password(_DEFAULT_PASSWORD),
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def _auth_ctx(user: UserModel) -> SimpleNamespace:
    token = create_access_token(user_id=user.id, role=user.role.value)
    return SimpleNamespace(
        user_id=user.id,
        email=user.email,
        password=_DEFAULT_PASSWORD,
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest_asyncio.fixture
async def admin_ctx(db_sessionmaker, clean_db) -> SimpleNamespace:
    return _auth_ctx(await _make_user(db_sessionmaker, UserRole.ADMIN))


@pytest_asyncio.fixture
async def staff_ctx(db_sessionmaker, clean_db) -> SimpleNamespace:
    return _auth_ctx(await _make_user(db_sessionmaker, UserRole.STAFF))


@pytest_asyncio.fixture
async def superadmin_ctx(db_sessionmaker, clean_db) -> SimpleNamespace:
    return _auth_ctx(await _make_user(db_sessionmaker, UserRole.SUPERADMIN))
