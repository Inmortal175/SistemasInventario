"""Mapeo centralizado de excepciones de dominio a respuestas HTTP.

La capa de dominio NUNCA conoce HTTP. Aquí es el único punto donde
traducimos DomainException → JSONResponse con el código de estado correcto.
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    CategoryDuplicateError,
    CategoryNotFoundError,
    DomainException,
    InsufficientPermissionsError,
    InsufficientStockError,
    InvalidCredentialsError,
    ItemNotFoundError,
    LocationCodeDuplicateError,
    LocationCodeInvalidError,
    LocationNotFoundError,
    MovementTypeNotAllowedError,
    ProductionRunNotFoundError,
    RateLimitExceededError,
    RecipeNotFoundError,
    RecipeProductionShortageError,
    StockBelowMinimumWarning,
    UserDuplicateError,
    UserNotFoundError,
    BatchNotFoundError,
)

logger = logging.getLogger(__name__)

# Cada excepción de dominio se mapea a un status HTTP.
_STATUS_MAP: dict[type[DomainException], int] = {
    # 404 — recursos no encontrados
    ItemNotFoundError: status.HTTP_404_NOT_FOUND,
    CategoryNotFoundError: status.HTTP_404_NOT_FOUND,
    LocationNotFoundError: status.HTTP_404_NOT_FOUND,
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    BatchNotFoundError: status.HTTP_404_NOT_FOUND,
    RecipeNotFoundError: status.HTTP_404_NOT_FOUND,
    ProductionRunNotFoundError: status.HTTP_404_NOT_FOUND,
    # 409 — conflicto de estado
    CategoryDuplicateError: status.HTTP_409_CONFLICT,
    LocationCodeDuplicateError: status.HTTP_409_CONFLICT,
    UserDuplicateError: status.HTTP_409_CONFLICT,
    # 403 — autorización
    InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
    MovementTypeNotAllowedError: status.HTTP_403_FORBIDDEN,
    # 422 — reglas de negocio / validación semántica
    InsufficientStockError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    LocationCodeInvalidError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    StockBelowMinimumWarning: status.HTTP_422_UNPROCESSABLE_ENTITY,
    RecipeProductionShortageError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    # 429 — rate limiting
    RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
    # 401 — autenticación
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
}


def _build_body(exc: DomainException, extra: dict | None = None) -> dict:
    body = {"error_code": exc.error_code, "message": exc.message}
    if extra:
        body.update(extra)
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainException)
    async def _domain_handler(request: Request, exc: DomainException) -> JSONResponse:
        http_status = _STATUS_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)

        extra: dict = {}
        headers: dict = {}
        # Adjuntar contexto útil según el tipo de excepción
        if isinstance(exc, InsufficientStockError):
            extra = {
                "available_stock": str(exc.available),
                "requested": str(exc.requested),
            }
        elif isinstance(exc, RecipeProductionShortageError):
            extra = {
                "supply_id": str(exc.supply_id),
                "required": str(exc.required),
                "available": str(exc.available),
            }
        elif isinstance(exc, RateLimitExceededError):
            headers["Retry-After"] = str(exc.retry_after_seconds)

        logger.warning(
            "DOMAIN_EXCEPTION code=%s status=%s path=%s",
            exc.error_code, http_status, request.url.path,
        )
        return JSONResponse(
            status_code=http_status, content=_build_body(exc, extra), headers=headers or None
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Los datos enviados no superan la validación",
                # jsonable_encoder serializa objetos no-JSON (p. ej. el ValueError
                # que Pydantic adjunta en ctx cuando un validador de campo falla).
                "details": jsonable_encoder(exc.errors()),
            },
        )
