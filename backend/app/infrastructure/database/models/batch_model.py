import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SupplyBatchModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Lote de un insumo perecedero — soporta FIFO y valorización (HU-13, HU-16).

    El stock total del insumo (`supply_items.current_stock`) es la suma de
    `current_stock` de todos los lotes activos.
    """
    __tablename__ = "supply_batches"

    __table_args__ = (
        CheckConstraint("current_stock >= 0", name="chk_batch_stock_non_negative"),
        CheckConstraint("unit_cost >= 0", name="chk_batch_cost_non_negative"),
    )

    supply_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("supply_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    batch_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    initial_stock: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    current_stock: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)

    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    # Evita re-emitir la alerta de vencimiento en cada corrida del cron (HU-13-03)
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    supply_item: Mapped["SupplyItemModel"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "SupplyItemModel", back_populates="batches", lazy="noload"
    )

    def __repr__(self) -> str:
        return (
            f"<SupplyBatchModel code={self.batch_code} "
            f"stock={self.current_stock} exp={self.expiration_date}>"
        )
