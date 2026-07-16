"""
Fixtures globales para toda la suite de pruebas.
Las fixtures de integración (BD real) se añadirán en el sprint de la capa API.
"""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.enums import UserRole, MovementType
from app.infrastructure.database.models.supply_model import SupplyItemModel
from app.infrastructure.database.models.user_model import UserModel


# ── Usuarios ficticios ────────────────────────────────────────────────────────

@pytest.fixture
def admin_user() -> UserModel:
    user = MagicMock(spec=UserModel)
    user.id = uuid.uuid4()
    user.role = UserRole.ADMIN
    user.is_active = True
    user.full_name = "Admin Test"
    return user


@pytest.fixture
def staff_user() -> UserModel:
    user = MagicMock(spec=UserModel)
    user.id = uuid.uuid4()
    user.role = UserRole.STAFF
    user.is_active = True
    user.full_name = "Staff Test"
    return user


# ── Insumos ficticios ─────────────────────────────────────────────────────────

@pytest.fixture
def supply_item_sufficient_stock() -> SupplyItemModel:
    """Insumo con stock suficiente para cualquier consumo razonable."""
    item = MagicMock(spec=SupplyItemModel)
    item.id = uuid.uuid4()
    item.name = "Harina de Trigo 000"
    item.current_stock = Decimal("25.000")
    item.minimum_stock = Decimal("10.000")
    item.maximum_stock = Decimal("100.000")
    item.is_active = True
    return item


@pytest.fixture
def supply_item_near_minimum() -> SupplyItemModel:
    """Insumo cuyo stock cae bajo el mínimo al consumir 5 unidades."""
    item = MagicMock(spec=SupplyItemModel)
    item.id = uuid.uuid4()
    item.name = "Harina de Trigo 000"
    item.current_stock = Decimal("12.000")
    item.minimum_stock = Decimal("10.000")
    item.maximum_stock = Decimal("100.000")
    item.is_active = True
    return item


@pytest.fixture
def supply_item_low_stock() -> SupplyItemModel:
    """Insumo con stock insuficiente para un consumo de 5 unidades."""
    item = MagicMock(spec=SupplyItemModel)
    item.id = uuid.uuid4()
    item.name = "Esencia de Vainilla"
    item.current_stock = Decimal("3.000")
    item.minimum_stock = Decimal("10.000")
    item.maximum_stock = Decimal("50.000")
    item.is_active = True
    return item


# ── Mocks de infraestructura ──────────────────────────────────────────────────

@pytest.fixture
def mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.sismember = AsyncMock(return_value=False)
    redis.sadd = AsyncMock(return_value=1)
    redis.srem = AsyncMock(return_value=1)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.publish = AsyncMock(return_value=1)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.ttl = AsyncMock(return_value=-2)
    redis.exists = AsyncMock(return_value=0)

    # scan_iter debe ser un async iterator, no un coroutine (para invalidación de caché)
    async def _scan_iter(match: str = "*"):
        for _ in ():
            yield _

    redis.scan_iter = _scan_iter
    return redis


@pytest.fixture
def mock_supply_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_movement_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_category_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_location_repo() -> AsyncMock:
    return AsyncMock()
