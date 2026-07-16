import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import LocationType, UnitMeasure


class RecipeItemInput(BaseModel):
    supply_item_id: uuid.UUID
    quantity_per_unit: Decimal = Field(gt=0, decimal_places=3)


class RecipeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    yield_unit: UnitMeasure = UnitMeasure.UNIT
    # HU-17: si se define, la receta crea automáticamente su producto terminado
    # (no se registra como insumo aparte) y lo ubica en `product_location_id`.
    product_name: str | None = Field(default=None, max_length=255)
    product_location_id: uuid.UUID | None = None
    shelf_life_days: int | None = Field(default=None, ge=0)
    items: list[RecipeItemInput] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_product(self) -> "RecipeCreate":
        if self.product_name and not self.product_location_id:
            raise ValueError("Indica la ubicación del producto terminado (refrigeradora)")
        return self


class RecipeItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    supply_item_id: uuid.UUID
    quantity_per_unit: Decimal


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    yield_unit: UnitMeasure
    produces_supply_item_id: uuid.UUID | None = None
    shelf_life_days: int | None = None
    is_active: bool
    items: list[RecipeItemResponse]


class RecipeListResponse(BaseModel):
    items: list[RecipeResponse]
    total: int


# ── Producción (HU-15) ───────────────────────────────────────────────────────

class ProductionRequest(BaseModel):
    recipe_id: uuid.UUID
    quantity: int = Field(gt=0, description="Unidades de producto final a producir")


class ProducedIngredient(BaseModel):
    supply_id: uuid.UUID
    supply_name: str
    consumed: Decimal
    movement_id: uuid.UUID


class ProductionResponse(BaseModel):
    recipe_id: uuid.UUID
    recipe_name: str
    quantity_produced: int
    ingredients: list[ProducedIngredient]
    # HU-17: registro de la corrida y del stock de producto terminado generado.
    production_id: uuid.UUID | None = None
    product_supply_item_id: uuid.UUID | None = None
    product_name: str | None = None
    product_new_stock: Decimal | None = None
    total_ingredient_cost: Decimal = Decimal("0")


# ── Historial de producción (HU-17) ──────────────────────────────────────────

class ProductionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    production_id: uuid.UUID
    recipe_id: uuid.UUID
    recipe_name: str
    product_supply_item_id: uuid.UUID | None
    product_name: str | None
    quantity_produced: Decimal
    total_ingredient_cost: Decimal
    performed_by_email: str
    created_at: datetime


class ProductionHistoryResponse(BaseModel):
    items: list[ProductionRunResponse]
    total: int
    page: int = 1
    limit: int = 20


# ── Lista de preparación de una corrida histórica (HU-17) ────────────────────

class PreparationBatch(BaseModel):
    batch_code: str
    expiration_date: date | None
    quantity: Decimal


class PreparationIngredient(BaseModel):
    supply_item_id: uuid.UUID
    supply_name: str
    unit: str
    location_code: str | None
    quantity_consumed: Decimal
    unit_cost: Decimal
    batches: list[PreparationBatch]


class ProductionPreparationResponse(BaseModel):
    """Cómo se fabricó una corrida: qué insumos, cuánto, en qué unidad y de dónde."""

    production_id: uuid.UUID
    recipe_name: str
    product_name: str | None
    quantity_produced: Decimal
    total_ingredient_cost: Decimal
    performed_by_email: str
    created_at: datetime
    ingredients: list[PreparationIngredient]


# ── Simulacro de stock / Dry-run (HU-15) ─────────────────────────────────────

class BatchPickPlan(BaseModel):
    """Un lote del que extraer, con cuánto sacar (previsualización FIFO, sin descontar)."""

    batch_code: str
    expiration_date: date | None
    take: Decimal


class SimulatedIngredient(BaseModel):
    supply_id: uuid.UUID
    supply_name: str
    required: Decimal
    available: Decimal
    sufficient: bool
    deficit: Decimal          # 0 si sufficient=True
    # Lista de preparación: dónde encontrarlo físicamente y de qué lotes sacarlo.
    unit: UnitMeasure
    location_code: str | None = None
    location_type: LocationType | None = None
    batch_plan: list[BatchPickPlan] = Field(default_factory=list)


class ProductionSimulationResponse(BaseModel):
    """Resultado del dry-run: NO modifica stock. Indica si la producción es viable."""

    recipe_id: uuid.UUID
    recipe_name: str
    quantity: int
    feasible: bool
    ingredients: list[SimulatedIngredient]
    missing: list[SimulatedIngredient]      # solo los insuficientes
