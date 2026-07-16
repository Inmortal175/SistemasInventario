import uuid
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.domain.enums import ItemType, UnitMeasure


class SupplyItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    sku: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    item_type: ItemType = ItemType.INGREDIENT
    category_id: uuid.UUID
    location_id: uuid.UUID
    unit_of_measure: UnitMeasure
    current_stock: Decimal = Field(ge=0, decimal_places=3)
    minimum_stock: Decimal = Field(ge=0, decimal_places=3)
    maximum_stock: Decimal = Field(ge=0, decimal_places=3)
    unit_cost: Decimal = Field(ge=0, decimal_places=4)
    is_perishable: bool = False
    expiration_date: date | None = None
    supplier_name: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_stock_range(self) -> "SupplyItemCreate":
        if self.minimum_stock > self.maximum_stock:
            raise ValueError("minimum_stock no puede superar maximum_stock")
        return self


class SupplyItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    category_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None
    minimum_stock: Decimal | None = Field(default=None, ge=0)
    maximum_stock: Decimal | None = Field(default=None, ge=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    expiration_date: date | None = None
    supplier_name: str | None = None


class SupplyItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    sku: str
    description: str | None
    item_type: ItemType
    category_id: uuid.UUID
    location_id: uuid.UUID
    unit_of_measure: UnitMeasure
    current_stock: Decimal
    minimum_stock: Decimal
    maximum_stock: Decimal
    unit_cost: Decimal
    is_perishable: bool
    expiration_date: date | None
    supplier_name: str | None
    is_active: bool
    is_below_minimum: bool          # propiedad calculada del modelo ORM


class SupplyItemListResponse(BaseModel):
    items: list[SupplyItemResponse]
    total: int
    low_stock_count: int            # cuántos items están bajo mínimo
    page: int = 1
    limit: int = 20
