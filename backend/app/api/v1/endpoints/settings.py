from typing import Annotated

from fastapi import APIRouter, Depends, Request, UploadFile

from app.api.v1.providers import SettingsServiceDep
from app.application.schemas.settings_schema import SettingsResponse, SettingsUpdate
from app.core.dependencies import require_roles
from app.core.uploads import MAX_BACKGROUND_BYTES, save_fitted_image, save_square_image
from app.domain.enums import LOGIN_BACKGROUND_SIZES, LoginBackgroundDevice, UserRole
from app.infrastructure.database.models.user_model import UserModel

router = APIRouter(prefix="/settings", tags=["Configuración"])

_SuperAdminOnly = Annotated[UserModel, Depends(require_roles(UserRole.SUPERADMIN))]


@router.get("", response_model=SettingsResponse)
async def get_settings(service: SettingsServiceDep) -> SettingsResponse:
    """Identidad visual del sistema. Sin autenticación: el login necesita el
    nombre, el logo y el tema antes de que exista una sesión."""
    return await service.get()


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    request: Request,
    payload: SettingsUpdate,
    service: SettingsServiceDep,
    current_user: _SuperAdminOnly,
) -> SettingsResponse:
    """Cambia el nombre, la paleta y las reglas de negocio de la instalación."""
    result = await service.update(payload, current_user.id)
    if payload.app_name:
        # Mantiene /docs y /openapi.json en sintonía con la interfaz.
        from app.main import apply_app_name

        apply_app_name(request.app, result.app_name)
    return result


@router.post("/logo", response_model=SettingsResponse)
async def upload_logo(
    file: UploadFile,
    service: SettingsServiceDep,
    current_user: _SuperAdminOnly,
) -> SettingsResponse:
    """Sube el logo del login (JPG/PNG/WebP, máx 2 MB). Se normaliza a 1:1."""
    logo_url = await save_square_image(file, subdir="branding", stem="logo")
    return await service.set_logo(logo_url, current_user.id)


@router.delete("/logo", response_model=SettingsResponse)
async def delete_logo(
    service: SettingsServiceDep,
    current_user: _SuperAdminOnly,
) -> SettingsResponse:
    """Vuelve al emblema por defecto del login."""
    return await service.clear_logo(current_user.id)


@router.post("/login-background/{device}", response_model=SettingsResponse)
async def upload_login_background(
    device: LoginBackgroundDevice,
    file: UploadFile,
    service: SettingsServiceDep,
    current_user: _SuperAdminOnly,
) -> SettingsResponse:
    """Sube el fondo del login para un dispositivo. Se recorta a su proporción."""
    url = await save_fitted_image(
        file,
        subdir="branding",
        stem=f"login_{device.value}",
        size=LOGIN_BACKGROUND_SIZES[device],
        fmt="JPEG",
        max_bytes=MAX_BACKGROUND_BYTES,
    )
    return await service.set_login_background(device, url, current_user.id)


@router.delete("/login-background/{device}", response_model=SettingsResponse)
async def delete_login_background(
    device: LoginBackgroundDevice,
    service: SettingsServiceDep,
    current_user: _SuperAdminOnly,
) -> SettingsResponse:
    """Quita el fondo de ese dispositivo; el login cae al del tamaño mayor."""
    return await service.clear_login_background(device, current_user.id)
