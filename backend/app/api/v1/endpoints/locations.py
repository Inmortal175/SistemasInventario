import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.providers import LocationServiceDep
from app.application.schemas.location_schema import (
    LocationCreate,
    LocationListResponse,
    LocationResponse,
)
from app.core.dependencies import CurrentUser, require_roles
from app.domain.enums import UserRole
from app.infrastructure.database.models.user_model import UserModel

router = APIRouter(prefix="/locations", tags=["Ubicaciones"])

# HU-03: solo ADMIN y SUPERADMIN administran ubicaciones físicas
_AdminOnly = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.SUPERADMIN))]


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    payload: LocationCreate,
    service: LocationServiceDep,
    current_user: _AdminOnly,
) -> LocationResponse:
    """HU-03: Registra una ubicación física rotulada. Solo ADMIN+."""
    return await service.create(data=payload, created_by_id=current_user.id)


@router.get("", response_model=LocationListResponse)
async def list_locations(
    service: LocationServiceDep,
    current_user: CurrentUser,   # cualquier usuario autenticado puede leer
) -> LocationListResponse:
    """Lista las ubicaciones activas ordenadas por código."""
    return await service.list_active()


@router.delete("/{location_id}", response_model=LocationResponse)
async def deactivate_location(
    location_id: uuid.UUID,
    service: LocationServiceDep,
    current_user: _AdminOnly,
) -> LocationResponse:
    """Desactivación lógica (soft-delete) de una ubicación."""
    return await service.deactivate(location_id)
