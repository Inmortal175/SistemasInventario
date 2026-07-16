from typing import Annotated

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.providers import AuthServiceDep, UserServiceDep
from app.application.schemas.auth_schema import LoginRequest, TokenResponse
from app.core.dependencies import CurrentUser
from app.core.uploads import save_square_image
from app.application.schemas.user_schema import (
    ChangePasswordRequest,
    ProfileUpdateRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _client_ip(request: Request) -> str:
    # Respeta el proxy inverso (X-Forwarded-For) si está presente.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
) -> TokenResponse:
    """Autentica con email (campo `username`) y contraseña. Devuelve JWT.

    HU-04-02: aplica rate limiting por IP (5 fallos / 15 min → bloqueo 900s).
    """
    return await service.login(
        LoginRequest(username=form.username, password=form.password),
        client_ip=_client_ip(request),
    )


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: CurrentUser) -> UserResponse:
    """Devuelve el perfil del usuario autenticado."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    payload: ProfileUpdateRequest,
    service: UserServiceDep,
    current_user: CurrentUser,
) -> UserResponse:
    """Actualiza el nombre del propio perfil (cualquier rol autenticado)."""
    return await service.update_own_profile(current_user.id, payload.full_name)


@router.patch("/me/password", response_model=UserResponse)
async def change_my_password(
    payload: ChangePasswordRequest,
    service: UserServiceDep,
    current_user: CurrentUser,
) -> UserResponse:
    """Cambia la propia contraseña verificando la actual (cualquier rol)."""
    return await service.change_own_password(
        current_user.id, payload.current_password, payload.new_password
    )


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile,
    service: UserServiceDep,
    current_user: CurrentUser,
) -> UserResponse:
    """Sube la foto de perfil (JPG/PNG/WebP, máx 2 MB). Se normaliza a 1:1.

    El menú y el perfil la muestran dentro de un círculo: sin recortar, una foto
    rectangular sale estirada.
    """
    avatar_url = await save_square_image(
        file, subdir="avatars", stem=str(current_user.id), size=256
    )
    return await service.update_avatar(current_user.id, avatar_url)


@router.delete("/me/avatar", response_model=UserResponse)
async def delete_avatar(
    service: UserServiceDep,
    current_user: CurrentUser,
) -> UserResponse:
    """Quita la foto de perfil y vuelve al ícono por defecto."""
    return await service.clear_avatar(current_user.id)

