import logging
import uuid

from redis.asyncio import Redis
from slugify import slugify

from app.application.schemas.category_schema import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
)
from app.domain.exceptions import CategoryDuplicateError, CategoryNotFoundError
from app.infrastructure.cache.cache_keys import (
    CATEGORIES_ACTIVE_INDEX,
    CATEGORY_NAMES_SET,
    category_key,
)
from app.infrastructure.cache.redis_client import (
    cache_delete,
    cache_get,
    cache_set,
)
from app.infrastructure.repositories.category_repository import CategoryRepository

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, repo: CategoryRepository, redis: Redis) -> None:
        self._repo = repo
        self._redis = redis

    async def create(
        self, data: CategoryCreate, created_by_id: uuid.UUID
    ) -> CategoryResponse:
        # ── 1. Detección de duplicado cache-first ────────────────────────────
        # Verificamos el Set Redis antes de tocar PostgreSQL (O(1))
        name_lower = data.name.lower()
        try:
            is_dup_in_cache = await self._redis.sismember(CATEGORY_NAMES_SET, name_lower)
        except Exception as exc:
            logger.warning("REDIS_UNAVAILABLE sismember err=%s", exc)
            is_dup_in_cache = False

        if is_dup_in_cache:
            raise CategoryDuplicateError(data.name)

        # ── 2. Fallback a PostgreSQL si Redis no tiene el Set poblado ────────
        existing = await self._repo.get_by_name(data.name)
        if existing:
            # Aprovechar para poblar el Set en Redis
            await self._add_name_to_cache_set(name_lower)
            raise CategoryDuplicateError(data.name)

        # ── 3. Persistir en PostgreSQL ────────────────────────────────────────
        slug = slugify(data.name)
        category = await self._repo.create(
            name=data.name,
            slug=slug,
            description=data.description,
            color_hex=data.color_hex.upper(),
            icon_name=data.icon_name,
            created_by=created_by_id,
        )

        # ── 4. Actualizar caché Redis ─────────────────────────────────────────
        response = CategoryResponse.model_validate(category)
        await cache_set(self._redis, category_key(str(category.id)), response.model_dump())
        await self._add_name_to_cache_set(name_lower)
        await cache_delete(self._redis, CATEGORIES_ACTIVE_INDEX)   # invalidar lista completa

        logger.info("CATEGORY_CREATED id=%s name=%s", category.id, category.name)
        return response

    async def list_active(self) -> CategoryListResponse:
        # ── Cache-first para lecturas de lista ───────────────────────────────
        cached = await cache_get(self._redis, CATEGORIES_ACTIVE_INDEX)
        if cached is not None:
            items = [CategoryResponse(**c) for c in cached["items"]]
            return CategoryListResponse(
                items=items, total=len(items), source="cache"
            )

        # ── PostgreSQL como fuente de verdad ─────────────────────────────────
        categories = await self._repo.list_active()
        items = [CategoryResponse.model_validate(c) for c in categories]
        payload = {"items": [i.model_dump() for i in items]}
        await cache_set(self._redis, CATEGORIES_ACTIVE_INDEX, payload)

        # Reconstruir el Set de nombres para futuros duplicate-checks
        if categories:
            try:
                await self._redis.sadd(
                    CATEGORY_NAMES_SET, *[c.name.lower() for c in categories]
                )
            except Exception as exc:
                logger.warning("REDIS_UNAVAILABLE sadd err=%s", exc)

        return CategoryListResponse(items=items, total=len(items), source="database")

    async def deactivate(self, category_id: uuid.UUID) -> CategoryResponse:
        category = await self._repo.deactivate(category_id)
        if category is None:
            raise CategoryNotFoundError(str(category_id))

        # Limpiar caché
        await cache_delete(
            self._redis,
            category_key(str(category_id)),
            CATEGORIES_ACTIVE_INDEX,
        )
        try:
            await self._redis.srem(CATEGORY_NAMES_SET, category.name.lower())
        except Exception as exc:
            logger.warning("REDIS_UNAVAILABLE srem err=%s", exc)

        return CategoryResponse.model_validate(category)

    async def _add_name_to_cache_set(self, name_lower: str) -> None:
        try:
            await self._redis.sadd(CATEGORY_NAMES_SET, name_lower)
        except Exception as exc:
            logger.warning("REDIS_UNAVAILABLE sadd err=%s", exc)
