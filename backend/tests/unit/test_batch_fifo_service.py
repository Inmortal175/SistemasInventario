"""HU-13-02: consumo FIFO por vencimiento con desglose por lote."""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.services.alert_service import AlertService
from app.application.services.batch_service import BatchService
from app.domain.enums import MovementType, UserRole
from app.domain.exceptions import InsufficientStockError


def _batch(code, stock, cost="1.0"):
    b = MagicMock()
    b.id = uuid.uuid4()
    b.batch_code = code
    b.current_stock = Decimal(stock)
    b.unit_cost = Decimal(cost)
    return b


def _make_service(mock_redis, item, batches, total_after):
    supply_repo = AsyncMock()
    supply_repo.get_by_id_for_update = AsyncMock(return_value=item)
    supply_repo.update_stock = AsyncMock()
    batch_repo = AsyncMock()
    batch_repo.list_active_fifo_for_update = AsyncMock(return_value=batches)
    batch_repo.apply_consumption = AsyncMock()
    batch_repo.sum_active_stock = AsyncMock(return_value=total_after)
    movement_repo = AsyncMock()
    created = MagicMock()
    created.id = uuid.uuid4()
    movement_repo.create = AsyncMock(return_value=created)
    service = BatchService(
        supply_repo=supply_repo,
        batch_repo=batch_repo,
        movement_repo=movement_repo,
        alert_service=AlertService(redis=mock_redis),
        redis=mock_redis,
    )
    return service, batch_repo


@pytest.mark.asyncio
async def test_fifo_consumes_oldest_batch_first(mock_redis):
    """SC-HU13-02: EXIT 15 de [A:10, B:20] → A=0 (inactivo) y B=15."""
    item = MagicMock()
    item.id = uuid.uuid4()
    item.name = "Leche Fresca"
    item.current_stock = Decimal("30.00")
    item.minimum_stock = Decimal("5.00")

    lote_a = _batch("A", "10.00")
    lote_b = _batch("B", "20.00")
    service, batch_repo = _make_service(
        mock_redis, item, [lote_a, lote_b], total_after=Decimal("15.00")
    )

    result = await service.consume_fifo(
        supply_id=item.id,
        quantity=Decimal("15.00"),
        performed_by_id=uuid.uuid4(),
        user_role=UserRole.STAFF,
        movement_type=MovementType.EXIT,
    )

    assert result.total_consumed == Decimal("15.00")
    assert result.new_total_stock == Decimal("15.00")
    assert len(result.breakdown) == 2
    assert result.breakdown[0].consumed == Decimal("10.00")   # Lote A completo
    assert result.breakdown[0].remaining == Decimal("0.00")
    assert result.breakdown[1].consumed == Decimal("5.00")    # 5 del Lote B
    assert result.breakdown[1].remaining == Decimal("15.00")
    # Se aplicó consumo a ambos lotes
    assert batch_repo.apply_consumption.await_count == 2


@pytest.mark.asyncio
async def test_fifo_insufficient_total_raises(mock_redis):
    """El total de lotes no cubre la cantidad → InsufficientStockError."""
    item = MagicMock()
    item.id = uuid.uuid4()
    item.name = "Crema"
    item.current_stock = Decimal("8.00")
    item.minimum_stock = Decimal("2.00")

    service, _ = _make_service(
        mock_redis, item, [_batch("A", "5.00"), _batch("B", "3.00")],
        total_after=Decimal("0"),
    )

    with pytest.raises(InsufficientStockError) as exc:
        await service.consume_fifo(
            supply_id=item.id,
            quantity=Decimal("20.00"),
            performed_by_id=uuid.uuid4(),
            user_role=UserRole.STAFF,
        )
    assert exc.value.available == Decimal("8.00")
    assert exc.value.requested == Decimal("20.00")
