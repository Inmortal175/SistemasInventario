import uuid

from sqlalchemy import Boolean, CheckConstraint, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import LocationType
from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Patrón idéntico al definido en domain/value_objects.py
_LOCATION_CODE_PATTERN = r"^(EST|REF|FRZ|CAB|CON|ALM)-\d{2}(-F\d{1,2})?$"


class LocationModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "locations"

    __table_args__ = (
        CheckConstraint(
            f"code ~ '{_LOCATION_CODE_PATTERN}'",
            name="chk_location_code_pattern",
        ),
    )

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_type: Mapped[LocationType] = mapped_column(
        SAEnum(LocationType, name="location_type", create_type=False),
        nullable=False,
    )
    capacity_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Trazabilidad HU-10-03: quién registró la ubicación (nullable por retrocompat).
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    supply_items: Mapped[list["SupplyItemModel"]] = relationship(  # type: ignore[name-defined]
        "SupplyItemModel", back_populates="location", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<LocationModel code={self.code} type={self.location_type}>"
