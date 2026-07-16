"""
TC-HIST-01 a TC-HIST-03 — HU-07: Historial de Movimientos por Insumo.
Pruebas unitarias del SupplyService.list_movements — sin BD, sin Redis real.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.services.alert_service import AlertService
from app.application.services.supply_service import SupplyService
from app.domain.enums import MovementType
from app.domain.exceptions import ItemNotFoundError
from app.infrastructure.database.models.movement_model import MovementHistoryModel


def _make_service(supply_repo, movement_repo, redis) -> SupplyService:
    return SupplyService(
        supply_repo=supply_repo,
        movement_repo=movement_repo,
        alert_service=AlertService(redis=redis),
        redis=redis,
    )


def _movement(movement_type: MovementType, notes: str | None = None) -> MagicMock:
    m = MagicMock(spec=MovementHistoryModel)
    m.id = uuid.uuid4()
    m.movement_type = movement_type
    m.quantity = Decimal("5.000")
    m.stock_before = Decimal("25.000")
    m.stock_after = Decimal("20.000")
    m.performed_by = uuid.uuid4()
    m.notes = notes
    m.alert_triggered = False
    m.created_at = datetime.now(timezone.utc)
    return m


# ── TC-HIST-01 — Consulta paginada con email del ejecutor ────────────────────

@pytest.mark.asyncio
async def test_TC_HIST_01_lists_movements_with_user_email(
    supply_item_sufficient_stock, mock_supply_repo, mock_movement_repo, mock_redis
):
    item = supply_item_sufficient_stock
    mock_supply_repo.get_by_id.return_value = item

    movement = _movement(MovementType.EXIT)
    mock_movement_repo.list_by_supply_item_with_user.return_value = [
        (movement, "pastelero@pasteleria.com")
    ]
    mock_movement_repo.count_by_supply_item.return_value = 1

    service = _make_service(mock_supply_repo, mock_movement_repo, mock_redis)
    result = await service.list_movements(supply_id=item.id, page=1, limit=50)

    assert result.total == 1
    assert result.page == 1
    assert result.limit == 50
    assert len(result.items) == 1
    row = result.items[0]
    assert row.user_email == "pastelero@pasteleria.com"
    assert row.executed_by_user_id == movement.performed_by
    assert row.is_adjustment is False
    assert row.adjustment_reason is None
    # El offset se calcula como (page-1)*limit
    mock_movement_repo.list_by_supply_item_with_user.assert_called_once_with(
        item.id, limit=50, offset=0
    )


# ── TC-HIST-02 — Un ADJUSTMENT marca is_adjustment y expone la razón ─────────

@pytest.mark.asyncio
async def test_TC_HIST_02_adjustment_exposes_reason(
    supply_item_sufficient_stock, mock_supply_repo, mock_movement_repo, mock_redis
):
    item = supply_item_sufficient_stock
    mock_supply_repo.get_by_id.return_value = item

    movement = _movement(MovementType.ADJUSTMENT_SUB, notes="Conteo físico")
    mock_movement_repo.list_by_supply_item_with_user.return_value = [
        (movement, "admin@pasteleria.com")
    ]
    mock_movement_repo.count_by_supply_item.return_value = 1

    service = _make_service(mock_supply_repo, mock_movement_repo, mock_redis)
    result = await service.list_movements(supply_id=item.id, page=2, limit=10)

    row = result.items[0]
    assert row.is_adjustment is True
    assert row.adjustment_reason == "Conteo físico"
    # page=2, limit=10 → offset=10
    mock_movement_repo.list_by_supply_item_with_user.assert_called_once_with(
        item.id, limit=10, offset=10
    )


# ── TC-HIST-03 — Insumo inexistente devuelve ItemNotFoundError ───────────────

@pytest.mark.asyncio
async def test_TC_HIST_03_unknown_supply_raises_not_found(
    mock_supply_repo, mock_movement_repo, mock_redis
):
    mock_supply_repo.get_by_id.return_value = None
    service = _make_service(mock_supply_repo, mock_movement_repo, mock_redis)

    with pytest.raises(ItemNotFoundError):
        await service.list_movements(supply_id=uuid.uuid4())

    mock_movement_repo.list_by_supply_item_with_user.assert_not_called()
    mock_movement_repo.count_by_supply_item.assert_not_called()
