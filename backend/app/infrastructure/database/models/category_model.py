import uuid
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CategoryModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dynamic_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False)       # Ej: #FF6B9D
    icon_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    creator: Mapped["UserModel"] = relationship(  # type: ignore[name-defined]
        "UserModel", back_populates="categories_created", lazy="noload"
    )
    supply_items: Mapped[list["SupplyItemModel"]] = relationship(  # type: ignore[name-defined]
        "SupplyItemModel", back_populates="category", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<CategoryModel id={self.id} name={self.name} slug={self.slug}>"
