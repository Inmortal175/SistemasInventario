import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import ItemType, UnitMeasure
from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SupplyItemModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "supply_items"

    __table_args__ = (
        CheckConstraint("current_stock >= 0", name="chk_stock_non_negative"),
        CheckConstraint("minimum_stock <= maximum_stock", name="chk_stock_range"),
        CheckConstraint("unit_cost >= 0", name="chk_cost_non_negative"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Insumo (materia prima) vs. producto terminado. Se guarda como texto — ver ItemType.
    item_type: Mapped[ItemType] = mapped_column(
        SAEnum(ItemType, native_enum=False, length=20),
        nullable=False,
        default=ItemType.INGREDIENT,
        server_default=ItemType.INGREDIENT.value,
        index=True,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dynamic_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    unit_of_measure: Mapped[UnitMeasure] = mapped_column(
        SAEnum(UnitMeasure, name="unit_measure", create_type=False),
        nullable=False,
    )

    # Numeric(10, 3) → hasta 9_999_999.999 con 3 decimales
    current_stock: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    minimum_stock: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    maximum_stock: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)

    # Numeric(12, 4) → costo unitario con 4 decimales
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=0)

    is_perishable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    supplier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Relaciones
    category: Mapped["CategoryModel"] = relationship(  # type: ignore[name-defined]
        "CategoryModel", back_populates="supply_items", lazy="noload"
    )
    location: Mapped["LocationModel"] = relationship(  # type: ignore[name-defined]
        "LocationModel", back_populates="supply_items", lazy="noload"
    )
    creator: Mapped["UserModel"] = relationship(  # type: ignore[name-defined]
        "UserModel", back_populates="supply_items_created", lazy="noload"
    )
    movements: Mapped[list["MovementHistoryModel"]] = relationship(  # type: ignore[name-defined]
        "MovementHistoryModel", back_populates="supply_item", lazy="noload"
    )
    batches: Mapped[list["SupplyBatchModel"]] = relationship(  # type: ignore[name-defined]
        "SupplyBatchModel", back_populates="supply_item", lazy="noload"
    )

    @property
    def is_below_minimum(self) -> bool:
        return self.current_stock < self.minimum_stock

    def __repr__(self) -> str:
        return f"<SupplyItemModel sku={self.sku} stock={self.current_stock}>"
