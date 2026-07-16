import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.category_icons import ALLOWED_CATEGORY_ICONS


def _validate_icon(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if value not in ALLOWED_CATEGORY_ICONS:
        allowed = ", ".join(sorted(ALLOWED_CATEGORY_ICONS))
        raise ValueError(f"Ícono no permitido. Opciones válidas: {allowed}")
    return value


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    color_hex: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$", examples=["#FF6B9D"])
    icon_name: str | None = Field(default=None, max_length=50, examples=["cake"])

    _check_icon = field_validator("icon_name")(_validate_icon)


class CategoryUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=500)
    color_hex: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon_name: str | None = Field(default=None, max_length=50)

    _check_icon = field_validator("icon_name")(_validate_icon)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    color_hex: str
    icon_name: str | None
    is_active: bool
    created_at: datetime


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
    total: int
    source: str = "database"    # "database" | "cache" — útil para debugging
