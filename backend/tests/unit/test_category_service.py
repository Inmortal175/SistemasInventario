"""
TC-CAT-SVC-01 a TC-CAT-SVC-03
Pruebas unitarias del CategoryService — sin BD, sin Redis real.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.schemas.category_schema import CategoryCreate
from app.application.services.category_service import CategoryService
from app.domain.exceptions import CategoryDuplicateError
from app.infrastructure.database.models.category_model import CategoryModel


def _make_service(repo: AsyncMock, redis: AsyncMock) -> CategoryService:
    return CategoryService(repo=repo, redis=redis)


def _make_category_model(name: str = "Harinas Especiales") -> MagicMock:
    cat = MagicMock(spec=CategoryModel)
    cat.id = uuid.uuid4()
    cat.name = name
    cat.slug = name.lower().replace(" ", "-")
    cat.description = None
    cat.color_hex = "#FFFFFF"
    cat.icon_name = None
    cat.is_active = True
    from datetime import datetime, timezone
    cat.created_at = datetime.now(timezone.utc)
    return cat


# ── TC-CAT-SVC-01 — Duplicado detectado en Redis sin consultar PostgreSQL ────

@pytest.mark.asyncio
async def test_TC_CAT_SVC_01_duplicate_detected_in_redis(
    mock_category_repo, mock_redis
):
    """Cache-first: si el nombre está en Redis Set → 409 sin tocar PostgreSQL."""
    mock_redis.sismember = AsyncMock(return_value=True)   # nombre en cache
    service = _make_service(mock_category_repo, mock_redis)

    data = CategoryCreate(name="Harinas Especiales", color_hex="#FFFFFF")

    with pytest.raises(CategoryDuplicateError) as exc_info:
        await service.create(data=data, created_by_id=uuid.uuid4())

    assert exc_info.value.error_code == "CATEGORY_NAME_ALREADY_EXISTS"
    mock_category_repo.get_by_name.assert_not_called()  # PostgreSQL no tocado
    mock_category_repo.create.assert_not_called()


# ── TC-CAT-SVC-02 — Duplicado detectado en PostgreSQL (Redis frío) ───────────

@pytest.mark.asyncio
async def test_TC_CAT_SVC_02_duplicate_detected_in_postgres_when_redis_cold(
    mock_category_repo, mock_redis
):
    """Redis miss → PostgreSQL tiene la categoría → 409 + poblar Redis Set."""
    mock_redis.sismember = AsyncMock(return_value=False)   # Redis frío
    mock_category_repo.get_by_name.return_value = _make_category_model()
    service = _make_service(mock_category_repo, mock_redis)

    data = CategoryCreate(name="Harinas Especiales", color_hex="#FFFFFF")

    with pytest.raises(CategoryDuplicateError):
        await service.create(data=data, created_by_id=uuid.uuid4())

    mock_category_repo.get_by_name.assert_called_once()
    mock_category_repo.create.assert_not_called()
    # El Set de Redis se pobló con el nombre encontrado
    mock_redis.sadd.assert_called()


# ── TC-CAT-SVC-03 — Creación exitosa persiste en DB y actualiza Redis ────────

@pytest.mark.asyncio
async def test_TC_CAT_SVC_03_successful_creation_persists_and_caches(
    mock_category_repo, mock_redis
):
    """Categoría nueva: PostgreSQL + Redis Set + cache individual + invalida índice."""
    mock_redis.sismember = AsyncMock(return_value=False)
    mock_category_repo.get_by_name.return_value = None    # no existe aún
    new_cat = _make_category_model("Colorantes Artificiales")
    mock_category_repo.create.return_value = new_cat

    service = _make_service(mock_category_repo, mock_redis)
    data = CategoryCreate(
        name="Colorantes Artificiales",
        color_hex="#FF6B9D",
        icon_name="tag",
    )

    result = await service.create(data=data, created_by_id=uuid.uuid4())

    assert result.name == "Colorantes Artificiales"
    mock_category_repo.create.assert_called_once()
    # Redis: se guardó la categoría individual y se invalidó el índice
    mock_redis.set.assert_called()
    mock_redis.delete.assert_called()
    mock_redis.sadd.assert_called()
