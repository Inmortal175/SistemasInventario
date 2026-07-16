import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BatchCreate(BaseModel):
    """HU-13-01 / HU-16-01: alta de lote de insumo perecedero."""

    quantity: Decimal = Field(gt=0, decimal_places=3)
    batch_code: str = Field(min_length=1, max_length=100)
    expiration_date: date | None = None
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)
    vendor_name: str | None = Field(default=None, max_length=255)


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    supply_item_id: uuid.UUID
    batch_code: str
    initial_stock: Decimal
    current_stock: Decimal
    unit_cost: Decimal
    vendor_name: str | None
    expiration_date: date | None
    is_active: bool


class BatchCreateResult(BaseModel):
    batch_id: uuid.UUID
    supply_id: uuid.UUID
    new_total_stock: Decimal
    total_movement_cost: Decimal


class BatchListResponse(BaseModel):
    items: list[BatchResponse]
    total: int
    total_stock: Decimal


class ConsumptionBreakdownItem(BaseModel):
    batch_id: uuid.UUID
    batch_code: str
    consumed: Decimal
    remaining: Decimal


class FifoConsumptionResponse(BaseModel):
    supply_id: uuid.UUID
    movement_id: uuid.UUID
    total_consumed: Decimal
    new_total_stock: Decimal
    alert_triggered: bool
    breakdown: list[ConsumptionBreakdownItem]


# ── Valorización financiera (HU-16-02) ───────────────────────────────────────

class FinancialsResponse(BaseModel):
    total_active_value: Decimal      # Σ stock_actual_i × unit_cost_i
    total_waste_loss: Decimal        # Σ quantity_wasted_j × unit_cost_batch_j
    active_batches_count: int
    period_start: date | None
