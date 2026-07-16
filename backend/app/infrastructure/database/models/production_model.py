import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProductionRunModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Corrida de producción (HU-17): asiento inmutable de cada vez que se produce.

    Registra qué receta se produjo, qué producto terminado y cuánto, el lote de
    producto generado, el costo total de los ingredientes consumidos y quién la
    ejecutó. Como `movement_history`, no se edita: es evidencia de auditoría.
    """
    __tablename__ = "production_runs"

    __table_args__ = (
        CheckConstraint("quantity_produced > 0", name="chk_production_qty_positive"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Producto terminado al que se sumó stock. Nullable si la receta no produce stock.
    product_supply_item_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("supply_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    # Lote de producto terminado creado por esta corrida (para FIFO/vencimiento).
    product_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("supply_batches.id", ondelete="RESTRICT"),
        nullable=True,
    )

    quantity_produced: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    total_ingredient_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=0
    )

    performed_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ProductionRunModel recipe={self.recipe_id} "
            f"qty={self.quantity_produced}>"
        )


class ProductionRunItemModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Snapshot inmutable de un insumo consumido en una corrida (lista de preparación).

    Copia al momento de producir: nombre, unidad, ubicación, cantidad y el desglose
    de lotes (JSON). Así el historial responde "¿de dónde salió, cuánto y en qué
    unidad?" aunque el insumo, su ubicación o sus lotes cambien o se borren después.
    """
    __tablename__ = "production_run_items"

    production_run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("production_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supply_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("supply_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supply_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    location_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quantity_consumed: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    # [{"batch_code": str, "expiration_date": "YYYY-MM-DD"|None, "quantity": str}]
    batch_breakdown: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ProductionRunItemModel run={self.production_run_id} "
            f"supply={self.supply_name} qty={self.quantity_consumed}>"
        )
