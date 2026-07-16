"""
TC-SVC-01 a TC-SVC-05
Pruebas unitarias del SupplyService — sin BD, sin Redis real.
"""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.schemas.movement_schema import MovementCreate
from app.application.services.alert_service import AlertService
from app.application.services.supply_service import SupplyService
from app.domain.enums import MovementType, UserRole
from app.domain.exceptions import (
    InsufficientStockError,
    ItemNotFoundError,
    MovementTypeNotAllowedError,
)
from app.infrastructure.database.models.movement_model import MovementHistoryModel


def _make_service(
    supply_repo: AsyncMock,
    movement_repo: AsyncMock,
    redis: AsyncMock,
) -> SupplyService:
    alert_service = AlertService(redis=redis)
    return SupplyService(
        supply_repo=supply_repo,
        movement_repo=movement_repo,
        alert_service=alert_service,
        redis=redis,
    )


# ── TC-SVC-01 — Stock insuficiente: no escribe en BD ─────────────────────────

@pytest.mark.asyncio
async def test_TC_SVC_01_insufficient_stock_raises_and_does_not_write(
    supply_item_low_stock, mock_supply_repo, mock_movement_repo, mock_redis
):
    """Valida que InsufficientStockError se lanza antes de cualquier escritura."""
    mock_supply_repo.get_by_id.return_value = supply_item_low_stock
    service = _make_service(mock_supply_repo, mock_movement_repo, mock_redis)

    data = MovementCreate(
        supply_item_id=supply_item_low_stock.id,
        movement_type=MovementType.EXIT,
        quantity=Decimal("5.000"),
    )

    with pytest.raises(InsufficientStockError) as exc_info:
        await service.register_movement(
            data=data,
            performed_by_id=uuid.uuid4(),
            user_role=UserRole.STAFF,
        )

    assert exc_info.value.available == Decimal("3.000")
    assert exc_info.value.requested == Decimal("5.000")
    assert exc_info.value.error_code == "INSUFFICIENT_STOCK"
    mock_movement_repo.create.assert_not_called()
    mock_supply_repo.update_stock.assert_not_called()


# ── TC-SVC-02 — STAFF no puede registrar ENTRY ───────────────────────────────

@pytest.mark.asyncio
async def test_TC_SVC_02_staff_cannot_register_entry(
    supply_item_sufficient_stock, mock_supply_repo, mock_movement_repo, mock_redis
):
    """RBAC: STAFF intenta ENTRY → MovementTypeNotAllowedError antes de tocar la BD."""
    mock_supply_repo.get_by_id.return_value = supply_item_sufficient_stock
    service = _make_service(mock_supply_repo, mock_movement_repo, mock_redis)

    data = MovementCreate(
        supply_item_id=supply_item_sufficient_stock.id,
        movement_type=MovementType.ENTRY,
        quantity=Decimal("10.000"),
    )

    with pytest.raises(MovementTypeNotAllowedError) as exc_info:
        await service.register_movement(
            data=data,
            performed_by_id=uuid.uuid4(),
            user_role=UserRole.STAFF,
        )

    assert exc_info.value.error_code == "MOVEMENT_TYPE_NOT_ALLOWED_FOR_ROLE"
    # La BD no debe ser consultada en ningún momento
    mock_supply_repo.get_by_id.assert_not_called()
    mock_movement_repo.create.assert_not_called()


# ── TC-SVC-03 — Consumo exitoso sin alerta ───────────────────────────────────

@pytest.mark.asyncio
async def test_TC_SVC_03_successful_exit_no_alert(
    supply_item_sufficient_stock, mock_supply_repo, mock_movement_repo, mock_redis
):
    """EXIT de 5 KG con stock=25: stock resultante=20 >= mínimo=10 → sin alerta."""
    item = supply_item_sufficient_stock

    # get_by_id se llama dos veces: primera lectura y get_by_id_for_update
    mock_supply_repo.get_by_id.return_value = item
    mock_supply_repo.get_by_id_for_update.return_value = item
    mock_supply_repo.update_stock.return_value = item

    movement_mock = MagicMock(spec=MovementHistoryModel)
    movement_mock.id = uuid.uuid4()
    movement_mock.supply_item_id = item.id
    movement_mock.movement_type = MovementType.EXIT
    movement_mock.quantity = Decimal("5.000")
    movement_mock.stock_before = Decimal("25.000")
    movement_mock.stock_after = Decimal("20.000")
    movement_mock.notes = None
    movement_mock.alert_triggered = False
    movement_mock.performed_by = uuid.uuid4()
    from datetime import datetime, timezone
    movement_mock.created_at = datetime.now(timezone.utc)
    mock_movement_repo.create.return_value = movement_mock

    service = _make_service(mock_supply_repo, mock_movement_repo, mock_redis)
    data = MovementCreate(
        supply_item_id=item.id,
        movement_type=MovementType.EXIT,
        quantity=Decimal("5.000"),
    )

    with patch.object(service._alert_service, "publish_low_stock") as mock_alert:
        result = await service.register_movement(
            data=data, performed_by_id=uuid.uuid4(), user_role=UserRole.STAFF
        )

    assert result.alert_triggered is False
    mock_alert.assert_not_called()
    mock_supply_repo.update_stock.assert_called_once()
    mock_movement_repo.create.assert_called_once()


# ── TC-SVC-04 — Consumo que activa alerta de stock crítico ───────────────────

@pytest.mark.asyncio
async def test_TC_SVC_04_exit_triggers_low_stock_alert(
    supply_item_near_minimum, mock_supply_repo, mock_movement_repo, mock_redis
):
    """EXIT de 5 KG con stock=12: resultado=7 < mínimo=10 → alerta publicada."""
    item = supply_item_near_minimum

    mock_supply_repo.get_by_id.return_value = item
    mock_supply_repo.get_by_id_for_update.return_value = item
    mock_supply_repo.update_stock.return_value = item

    movement_mock = MagicMock(spec=MovementHistoryModel)
    movement_mock.id = uuid.uuid4()
    movement_mock.supply_item_id = item.id
    movement_mock.movement_type = MovementType.EXIT
    movement_mock.quantity = Decimal("5.000")
    movement_mock.stock_before = Decimal("12.000")
    movement_mock.stock_after = Decimal("7.000")
    movement_mock.notes = None
    movement_mock.alert_triggered = True
    movement_mock.performed_by = uuid.uuid4()
    from datetime import datetime, timezone
    movement_mock.created_at = datetime.now(timezone.utc)
    mock_movement_repo.create.return_value = movement_mock

    service = _make_service(mock_supply_repo, mock_movement_repo, mock_redis)
    data = MovementCreate(
        supply_item_id=item.id,
        movement_type=MovementType.EXIT,
        quantity=Decimal("5.000"),
    )

    with patch.object(service._alert_service, "publish_low_stock") as mock_alert:
        result = await service.register_movement(
            data=data, performed_by_id=uuid.uuid4(), user_role=UserRole.STAFF
        )

    assert result.alert_triggered is True
    mock_alert.assert_called_once_with(
        supply_item_id=item.id,
        supply_name=item.name,
        current_stock=Decimal("7.000"),
        minimum_stock=item.minimum_stock,
    )


# ── TC-SVC-05 — Insumo inactivo devuelve ItemNotFoundError ───────────────────

@pytest.mark.asyncio
async def test_TC_SVC_05_inactive_item_raises_not_found(
    mock_supply_repo, mock_movement_repo, mock_redis
):
    """Un insumo con is_active=False no existe para el sistema."""
    mock_supply_repo.get_by_id.return_value = None   # inactivo → repo devuelve None
    service = _make_service(mock_supply_repo, mock_movement_repo, mock_redis)

    data = MovementCreate(
        supply_item_id=uuid.uuid4(),
        movement_type=MovementType.EXIT,
        quantity=Decimal("1.000"),
    )

    with pytest.raises(ItemNotFoundError) as exc_info:
        await service.register_movement(
            data=data, performed_by_id=uuid.uuid4(), user_role=UserRole.ADMIN
        )

    assert exc_info.value.error_code == "SUPPLY_ITEM_NOT_FOUND_OR_INACTIVE"
    mock_movement_repo.create.assert_not_called()


# ── TC-SVC-06 — Detalle de insumo inexistente → ItemNotFoundError ────────────

@pytest.mark.asyncio
async def test_TC_SVC_06_get_detail_missing_raises_not_found(
    mock_supply_repo, mock_movement_repo, mock_redis
):
    """get_detail de un id inexistente lanza ItemNotFoundError (→ 404)."""
    mock_supply_repo.get_by_id.return_value = None
    service = _make_service(mock_supply_repo, mock_movement_repo, mock_redis)

    with pytest.raises(ItemNotFoundError) as exc_info:
        await service.get_detail(uuid.uuid4())

    assert exc_info.value.error_code == "SUPPLY_ITEM_NOT_FOUND_OR_INACTIVE"
