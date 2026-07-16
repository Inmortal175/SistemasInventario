from decimal import Decimal


class DomainException(Exception):
    """Base para todas las excepciones de dominio del negocio."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


# ── Inventario / Stock ───────────────────────────────────────────────────────

class InsufficientStockError(DomainException):
    """Se intenta retirar más cantidad de la disponible."""

    def __init__(self, available: Decimal, requested: Decimal, item_name: str = "") -> None:
        self.available = available
        self.requested = requested
        self.item_name = item_name
        super().__init__(
            message=(
                f"Stock insuficiente para '{item_name}': "
                f"disponible {available}, solicitado {requested}"
            ),
            error_code="INSUFFICIENT_STOCK",
        )


class ItemNotFoundError(DomainException):
    """Insumo no existe o está dado de baja."""

    def __init__(self, item_id: str) -> None:
        super().__init__(
            message=f"Insumo con id '{item_id}' no encontrado o inactivo",
            error_code="SUPPLY_ITEM_NOT_FOUND_OR_INACTIVE",
        )


class StockBelowMinimumWarning(DomainException):
    """El stock resultante cae bajo el mínimo configurado.
    No es un error bloqueante; se propaga para disparar alerta."""

    def __init__(self, item_name: str, current: Decimal, minimum: Decimal) -> None:
        self.current = current
        self.minimum = minimum
        self.deficit = minimum - current
        super().__init__(
            message=(
                f"Alerta: '{item_name}' en stock crítico "
                f"({current} < mínimo {minimum})"
            ),
            error_code="STOCK_BELOW_MINIMUM",
        )


# ── Categorías ───────────────────────────────────────────────────────────────

class CategoryDuplicateError(DomainException):
    """Ya existe una categoría activa con ese nombre."""

    def __init__(self, name: str) -> None:
        super().__init__(
            message=f"Ya existe una categoría activa con nombre '{name}'",
            error_code="CATEGORY_NAME_ALREADY_EXISTS",
        )


class CategoryNotFoundError(DomainException):
    """Categoría no existe o está inactiva."""

    def __init__(self, category_id: str) -> None:
        super().__init__(
            message=f"Categoría '{category_id}' no encontrada o inactiva",
            error_code="CATEGORY_NOT_FOUND",
        )


# ── Ubicaciones ──────────────────────────────────────────────────────────────

class LocationCodeInvalidError(DomainException):
    """El código de ubicación no cumple el patrón obligatorio."""

    PATTERN_EXAMPLE = "EST-01, EST-01-F2, REF-02, FRZ-01, CAB-03, CON-01, ALM-01"

    def __init__(self, code: str) -> None:
        super().__init__(
            message=(
                f"Código de ubicación '{code}' inválido. "
                f"Formato esperado: {self.PATTERN_EXAMPLE}"
            ),
            error_code="LOCATION_CODE_INVALID",
        )


class LocationNotFoundError(DomainException):
    """Ubicación física no existe o está inactiva."""

    def __init__(self, location_id: str) -> None:
        super().__init__(
            message=f"Ubicación '{location_id}' no encontrada o inactiva",
            error_code="LOCATION_NOT_FOUND",
        )


class LocationCodeDuplicateError(DomainException):
    """Ya existe una ubicación activa con ese código."""

    def __init__(self, code: str) -> None:
        super().__init__(
            message=f"Ya existe una ubicación activa con código '{code}'",
            error_code="LOCATION_CODE_ALREADY_EXISTS",
        )


# ── Autorización / RBAC ──────────────────────────────────────────────────────

class InsufficientPermissionsError(DomainException):
    """El rol del usuario no tiene acceso al recurso o acción."""

    def __init__(self, required_roles: list[str] | None = None) -> None:
        roles_str = ", ".join(required_roles) if required_roles else "superiores"
        super().__init__(
            message=f"Acción no permitida. Se requieren roles: {roles_str}",
            error_code="INSUFFICIENT_PERMISSIONS",
        )


class MovementTypeNotAllowedError(DomainException):
    """El rol del usuario no puede registrar ese tipo de movimiento."""

    def __init__(self, movement_type: str, allowed: list[str]) -> None:
        super().__init__(
            message=(
                f"Tipo de movimiento '{movement_type}' no permitido para su rol. "
                f"Permitidos: {allowed}"
            ),
            error_code="MOVEMENT_TYPE_NOT_ALLOWED_FOR_ROLE",
        )


class InvalidCredentialsError(DomainException):
    """Credenciales de acceso inválidas (HU-04). Se traduce a HTTP 401."""

    def __init__(self) -> None:
        super().__init__(
            message="Credenciales inválidas",
            error_code="INVALID_CREDENTIALS",
        )


class RateLimitExceededError(DomainException):
    """Se superó el límite de intentos permitidos (HU-04-02)."""

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            message=(
                f"Demasiados intentos fallidos. Reintente en {retry_after_seconds} segundos."
            ),
            error_code="RATE_LIMIT_EXCEEDED",
        )


# ── Usuarios (HU-10) ─────────────────────────────────────────────────────────

class UserNotFoundError(DomainException):
    """Usuario no existe."""

    def __init__(self, user_id: str) -> None:
        super().__init__(
            message=f"Usuario '{user_id}' no encontrado",
            error_code="USER_NOT_FOUND",
        )


class UserDuplicateError(DomainException):
    """Ya existe un usuario con ese email."""

    def __init__(self, email: str) -> None:
        super().__init__(
            message=f"Ya existe un usuario con email '{email}'",
            error_code="USER_EMAIL_ALREADY_EXISTS",
        )


# ── Lotes / Producción (HU-13, HU-15) ────────────────────────────────────────

class BatchNotFoundError(DomainException):
    """Lote no existe o está inactivo."""

    def __init__(self, batch_id: str) -> None:
        super().__init__(
            message=f"Lote '{batch_id}' no encontrado o inactivo",
            error_code="BATCH_NOT_FOUND",
        )


class RecipeNotFoundError(DomainException):
    """Receta no existe o está inactiva."""

    def __init__(self, recipe_id: str) -> None:
        super().__init__(
            message=f"Receta '{recipe_id}' no encontrada o inactiva",
            error_code="RECIPE_NOT_FOUND",
        )


class ProductionRunNotFoundError(DomainException):
    """Corrida de producción no existe."""

    def __init__(self, production_id: str) -> None:
        super().__init__(
            message=f"Corrida de producción '{production_id}' no encontrada",
            error_code="PRODUCTION_RUN_NOT_FOUND",
        )


class RecipeProductionShortageError(DomainException):
    """Stock insuficiente de al menos un ingrediente al producir una receta.

    Provoca ROLLBACK atómico: no se descuenta ningún insumo (HU-15 SC-02).
    """

    def __init__(self, supply_id: str, required: Decimal, available: Decimal) -> None:
        self.supply_id = supply_id
        self.required = required
        self.available = available
        super().__init__(
            message=(
                f"Producción abortada: stock insuficiente del insumo '{supply_id}' "
                f"(requerido {required}, disponible {available})"
            ),
            error_code="RECIPE_PRODUCTION_FAILED_STOCK_SHORTAGE",
        )
