import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.providers import UserServiceDep
from app.application.schemas.user_schema import (
    PasswordResetRequest,
    UserAuditLogResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
)
from app.core.dependencies import require_roles
from app.domain.enums import UserRole
from app.infrastructure.database.models.user_model import UserModel

router = APIRouter(prefix="/users", tags=["Usuarios"])

# HU-10: la gestión de cuentas y trazabilidad global es exclusiva de SUPERADMIN.
_SuperAdminOnly = Annotated[UserModel, Depends(require_roles(UserRole.SUPERADMIN))]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    service: UserServiceDep,
    current_user: _SuperAdminOnly,
) -> UserResponse:
    """HU-10-01: Crea una cuenta con rol asignado (contraseña con Bcrypt)."""
    return await service.create_user(payload)


@router.get("", response_model=UserListResponse)
async def list_users(
    service: UserServiceDep,
    current_user: _SuperAdminOnly,
) -> UserListResponse:
    """Lista los usuarios del sistema, activos y suspendidos."""
    return await service.list_users()


@router.patch("/{user_id}/suspend", response_model=UserResponse)
async def suspend_user(
    user_id: uuid.UUID,
    service: UserServiceDep,
    current_user: _SuperAdminOnly,
) -> UserResponse:
    """HU-10-02: Suspensión lógica + invalidación de sesión (blacklist Redis)."""
    return await service.suspend(user_id)


@router.patch("/{user_id}/reactivate", response_model=UserResponse)
async def reactivate_user(
    user_id: uuid.UUID,
    service: UserServiceDep,
    current_user: _SuperAdminOnly,
) -> UserResponse:
    """Reactiva una cuenta suspendida y limpia su blacklist."""
    return await service.reactivate(user_id)


@router.patch("/{user_id}/password", response_model=UserResponse)
async def reset_user_password(
    user_id: uuid.UUID,
    payload: PasswordResetRequest,
    service: UserServiceDep,
    current_user: _SuperAdminOnly,
) -> UserResponse:
    """Restablece la contraseña de un usuario e invalida sus sesiones activas.

    Medio de recuperación para usuarios que olvidan su clave. Solo SUPERADMIN.
    """
    return await service.reset_password(user_id, payload.new_password)


@router.get("/{user_id}/audit-log", response_model=UserAuditLogResponse)
async def user_audit_log(
    user_id: uuid.UUID,
    service: UserServiceDep,
    current_user: _SuperAdminOnly,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UserAuditLogResponse:
    """HU-10-03: Historial consolidado de mutaciones realizadas por el usuario."""
    return await service.get_audit_log(user_id, page=page, limit=limit)
