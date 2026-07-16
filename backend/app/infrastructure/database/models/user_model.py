import uuid
from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import UserRole
from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_type=False),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relaciones (lazy="noload" por defecto en async — cargar explícitamente)
    categories_created: Mapped[list["CategoryModel"]] = relationship(  # type: ignore[name-defined]
        "CategoryModel", back_populates="creator", lazy="noload"
    )
    supply_items_created: Mapped[list["SupplyItemModel"]] = relationship(  # type: ignore[name-defined]
        "SupplyItemModel", back_populates="creator", lazy="noload"
    )
    movements_performed: Mapped[list["MovementHistoryModel"]] = relationship(  # type: ignore[name-defined]
        "MovementHistoryModel", back_populates="performer", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<UserModel id={self.id} email={self.email} role={self.role}>"
