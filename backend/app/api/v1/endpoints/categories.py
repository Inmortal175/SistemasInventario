import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.v1.providers import CategoryServiceDep
from app.application.schemas.category_schema import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
)
from app.core.dependencies import CurrentUser, require_roles
from app.domain.enums import UserRole
from app.infrastructure.database.models.user_model import UserModel

router = APIRouter(prefix="/categories", tags=["Categorías"])

# HU-01: solo ADMIN y SUPERADMIN pueden crear/desactivar categorías
_AdminOnly = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.SUPERADMIN))]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    service: CategoryServiceDep,
    current_user: _AdminOnly,
    response: Response,
) -> CategoryResponse:
    """HU-01: Crea una categoría dinámica (PostgreSQL + índice Redis)."""
    result = await service.create(data=payload, created_by_id=current_user.id)
    response.headers["X-Cache-Status"] = "WRITE"
    return result


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    service: CategoryServiceDep,
    current_user: CurrentUser,   # cualquier usuario autenticado puede leer
) -> CategoryListResponse:
    """Lista las categorías activas (cache-first desde Redis)."""
    return await service.list_active()


@router.delete("/{category_id}", response_model=CategoryResponse)
async def deactivate_category(
    category_id: uuid.UUID,
    service: CategoryServiceDep,
    current_user: _AdminOnly,
) -> CategoryResponse:
    """Desactivación lógica (soft-delete) de una categoría."""
    return await service.deactivate(category_id)
