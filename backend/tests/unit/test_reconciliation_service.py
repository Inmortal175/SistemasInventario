"""HU-11: conciliación de inventario (ADJUSTMENT trazable)."""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.services.alert_service import AlertService
from app.application.services.supply_service import SupplyService
from app.domain.enums import MovementType


def _make_service(mock_redis, item):
    supply_repo = AsyncMock()
    supply_repo.get_by_id_for_update = AsyncMock(return_value=item)
    supply_repo.update_stock = AsyncMock()
    movement_repo = AsyncMock()
    created = MagicMock()
    created.id = uuid.uuid4()
    movement_repo.create = AsyncMock(return_value=created)
    service = SupplyService(
        supply_repo=supply_repo,
        movement_repo=movement_repo,
        alert_service=AlertService(redis=mock_redis),
        redis=mock_redis,
    )
    return service, supply_repo, movement_repo


@pytest.mark.asyncio
async def test_reconcile_negative_delta_records_adjustment_sub(mock_redis):
    """SC-HU11-01: 15.000 → 13.500 (Δ=-1.500) registra ADJUSTMENT_SUB."""
    item = MagicMock()
    item.id = uuid.uuid4()
    item.name = "Mantequilla Sin Sal"
    item.current_stock = Decimal("15.000")
    item.minimum_stock = Decimal("5.000")

    service, supply_repo, movement_repo = _make_service(mock_redis, item)
    result = await service.reconcile(
        supply_id=item.id,
        physical_stock=Decimal("13.500"),
        reason="Error de digitación",
        performed_by_id=uuid.uuid4(),
    )

    assert result.delta == Decimal("-1.500")
    assert result.stock_after == Decimal("13.500")
    assert result.alert_triggered is False
    supply_repo.update_stock.assert_awaited_once()
    _, kwargs = movement_repo.create.call_args
    assert kwargs["movement_type"] == MovementType.ADJUSTMENT_SUB
    assert kwargs["quantity"] == Decimal("1.500")
    assert kwargs["notes"] == "Error de digitación"


@pytest.mark.asyncio
async def test_reconcile_below_minimum_triggers_alert(mock_redis):
    """SC-HU11-03: ajuste a 12.000 con mínimo 15.000 dispara alerta."""
    item = MagicMock()
    item.id = uuid.uuid4()
    item.name = "Leche Fresca"
    item.current_stock = Decimal("20.000")
    item.minimum_stock = Decimal("15.000")

    service, _, movement_repo = _make_service(mock_redis, item)
    result = await service.reconcile(
        supply_id=item.id,
        physical_stock=Decimal("12.000"),
        reason="Merma física",
        performed_by_id=uuid.uuid4(),
    )

    assert result.alert_triggered is True
    mock_redis.publish.assert_awaited()
    _, kwargs = movement_repo.create.call_args
    assert kwargs["alert_triggered"] is True
