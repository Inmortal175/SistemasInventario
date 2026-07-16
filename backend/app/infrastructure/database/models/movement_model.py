import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import MovementType
from app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin


class MovementHistoryModel(Base, UUIDPrimaryKeyMixin):
    """Historial de movimientos — INMUTABLE por diseño de auditoría.

    Decisión: NO hereda TimestampMixin porque no tiene updated_at.
    Un movimiento registrado nunca puede modificarse; solo existe created_at.
    """
    __tablename__ = "movement_history"

    supply_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("supply_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    movement_type: Mapped[MovementType] = mapped_column(
        SAEnum(MovementType, name="movement_type", create_type=False),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    stock_before: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    stock_after: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)

    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    alert_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # HU-16: costo unitario del movimiento (p. ej. ENTRY de un lote con precio).
    # total_movement_cost = quantity * unit_cost se calcula en la capa de aplicación.
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)

    performed_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # created_at del servidor — garantiza que el cliente no puede manipular la fecha
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relaciones
    supply_item: Mapped["SupplyItemModel"] = relationship(  # type: ignore[name-defined]
        "SupplyItemModel", back_populates="movements", lazy="noload"
    )
    performer: Mapped["UserModel"] = relationship(  # type: ignore[name-defined]
        "UserModel", back_populates="movements_performed", lazy="noload"
    )

    def __repr__(self) -> str:
        return (
            f"<MovementHistoryModel type={self.movement_type} "
            f"qty={self.quantity} after={self.stock_after}>"
        )
