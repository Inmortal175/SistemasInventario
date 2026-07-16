import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.domain.enums import MovementType


class MovementCreate(BaseModel):
    supply_item_id: uuid.UUID
    movement_type: MovementType
    quantity: Decimal = Field(gt=0, decimal_places=3)
    notes: str | None = Field(default=None, max_length=500)


class ReconciliationRequest(BaseModel):
    """HU-11: ajuste de stock por conteo físico."""

    supply_id: uuid.UUID
    physical_stock: Decimal = Field(ge=0, decimal_places=3)
    reason: str = Field(min_length=3, max_length=500)


class ReconciliationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: uuid.UUID
    supply_id: uuid.UUID
    delta: Decimal
    stock_before: Decimal
    stock_after: Decimal
    alert_triggered: bool


class MovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    supply_item_id: uuid.UUID
    movement_type: MovementType
    quantity: Decimal
    stock_before: Decimal
    stock_after: Decimal
    notes: str | None
    alert_triggered: bool
    performed_by: uuid.UUID
    created_at: datetime


class MovementHistoryItem(BaseModel):
    """HU-07: fila de auditoría con trazabilidad de usuario (email)."""

    movement_id: uuid.UUID
    movement_type: MovementType
    quantity: Decimal
    stock_before: Decimal
    stock_after: Decimal
    executed_by_user_id: uuid.UUID
    user_email: str
    is_adjustment: bool
    adjustment_reason: str | None
    notes: str | None
    alert_triggered: bool
    created_at: datetime


class MovementHistoryListResponse(BaseModel):
    items: list[MovementHistoryItem]
    total: int
    page: int
    limit: int
