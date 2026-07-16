import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.domain.enums import LocationType
from app.domain.value_objects import LocationCode
from app.domain.exceptions import LocationCodeInvalidError


class LocationCreate(BaseModel):
    code: str = Field(min_length=4, max_length=20, examples=["EST-01-F2", "REF-02"])
    description: str | None = Field(default=None, max_length=255)
    location_type: LocationType
    capacity_units: int | None = Field(default=None, ge=1)

    @field_validator("code")
    @classmethod
    def validate_location_code(cls, v: str) -> str:
        try:
            return str(LocationCode.parse(v))
        except LocationCodeInvalidError as exc:
            raise ValueError(exc.message) from exc


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    description: str | None
    location_type: LocationType
    capacity_units: int | None
    is_active: bool


class LocationListResponse(BaseModel):
    items: list[LocationResponse]
    total: int
