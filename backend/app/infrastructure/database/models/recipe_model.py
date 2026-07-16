import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import UnitMeasure
from sqlalchemy import Enum as SAEnum
from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RecipeModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Receta / Bill of Materials para producción automatizada (HU-15)."""
    __tablename__ = "recipes"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    yield_unit: Mapped[UnitMeasure] = mapped_column(
        SAEnum(UnitMeasure, name="unit_measure", create_type=False),
        nullable=False,
        default=UnitMeasure.UNIT,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Producto terminado que genera esta receta (HU-17). Nullable: recetas antiguas
    # o recetas que solo consumen sin producir stock trazable.
    produces_supply_item_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("supply_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    # Vida útil del producto terminado en días (para el vencimiento del lote producido).
    shelf_life_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    produces: Mapped["SupplyItemModel"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "SupplyItemModel", lazy="noload", foreign_keys=[produces_supply_item_id]
    )

    items: Mapped[list["RecipeItemModel"]] = relationship(
        "RecipeItemModel",
        back_populates="recipe",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<RecipeModel name={self.name}>"


class RecipeItemModel(Base, UUIDPrimaryKeyMixin):
    """Ingrediente de una receta: cuánto insumo se consume por unidad producida."""
    __tablename__ = "recipe_items"

    __table_args__ = (
        UniqueConstraint("recipe_id", "supply_item_id", name="uq_recipe_supply"),
        CheckConstraint("quantity_per_unit > 0", name="chk_recipe_qty_positive"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    supply_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("supply_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)

    recipe: Mapped["RecipeModel"] = relationship(
        "RecipeModel", back_populates="items", lazy="noload"
    )
    supply_item: Mapped["SupplyItemModel"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "SupplyItemModel", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<RecipeItemModel supply={self.supply_item_id} qty={self.quantity_per_unit}>"
