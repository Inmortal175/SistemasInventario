import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.domain.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.STAFF


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class ProfileUpdateRequest(BaseModel):
    """Actualización del propio perfil (self-service)."""

    full_name: str = Field(min_length=2, max_length=255)


class ChangePasswordRequest(BaseModel):
    """Cambio de la propia contraseña, verificando la actual."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    avatar_url: str | None = None
    created_at: datetime


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int


class AuditLogEntry(BaseModel):
    """Una acción mutadora ejecutada por un usuario (HU-10-03)."""

    action_type: str          # CATEGORY_CREATED | LOCATION_CREATED | MOVEMENT_<TYPE>
    entity_id: uuid.UUID
    summary: str
    timestamp: datetime


class UserAuditLogResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    total: int
    entries: list[AuditLogEntry]
    page: int = 1
    limit: int = 20
