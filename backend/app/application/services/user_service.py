import logging
import uuid

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.application.schemas.user_schema import (
    AuditLogEntry,
    UserAuditLogResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
)
from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.core.uploads import delete_static_file
from app.domain.enums import MovementType, UnitMeasure
from app.domain.exceptions import (
    InvalidCredentialsError,
    UserDuplicateError,
    UserNotFoundError,
)

# Etiquetas de auditoría en español (capa de aplicación: es texto de presentación
# del historial, no lógica de dominio).
_MOVEMENT_VERB: dict[MovementType, str] = {
    MovementType.ENTRY: "Ingreso",
    MovementType.EXIT: "Salida",
    MovementType.WASTE: "Merma",
    MovementType.ADJUSTMENT_ADD: "Ajuste (+)",
    MovementType.ADJUSTMENT_SUB: "Ajuste (−)",
    MovementType.TRANSFER: "Traslado",
}

_UNIT_ABBR: dict[UnitMeasure, str] = {
    UnitMeasure.KG: "kg", UnitMeasure.GR: "g", UnitMeasure.L: "L", UnitMeasure.ML: "ml",
    UnitMeasure.UNIT: "u", UnitMeasure.PKG: "paq", UnitMeasure.BOX: "caja",
    UnitMeasure.DOZEN: "doc",
}


def _fmt_qty(value: object) -> str:
    """Formatea una cantidad Decimal quitando ceros finales innecesarios."""
    s = f"{value}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def _clean_reason(notes: str | None) -> str | None:
    """Extrae un motivo legible de las notas, sin el desglose técnico por lotes."""
    if not notes:
        return None
    reason = notes.split(" FIFO")[0].split(" (lote")[0].strip()
    return reason or None
from app.infrastructure.cache.cache_keys import (
    token_blacklist_key,
    token_valid_from_key,
)
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.infrastructure.repositories.location_repository import LocationRepository
from app.infrastructure.repositories.movement_repository import MovementRepository
from app.infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """HU-10: gestión de usuarios y trazabilidad global (SUPERADMIN)."""

    def __init__(
        self,
        user_repo: UserRepository,
        category_repo: CategoryRepository,
        location_repo: LocationRepository,
        movement_repo: MovementRepository,
        redis: Redis,
    ) -> None:
        self._users = user_repo
        self._categories = category_repo
        self._locations = location_repo
        self._movements = movement_repo
        self._redis = redis
        self._settings = get_settings()

    async def create_user(self, data: UserCreate) -> UserResponse:
        existing = await self._users.get_by_email(data.email)
        if existing:
            raise UserDuplicateError(data.email)
        user = await self._users.create(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
            is_active=True,
        )
        logger.info("USER_CREATED id=%s email=%s role=%s", user.id, user.email, user.role)
        return UserResponse.model_validate(user)

    async def list_users(self) -> UserListResponse:
        users = await self._users.list_all()
        items = [UserResponse.model_validate(u) for u in users]
        return UserListResponse(items=items, total=len(items))

    async def suspend(self, user_id: uuid.UUID) -> UserResponse:
        """HU-10-02: desactiva el usuario e invalida su sesión JWT vía blacklist.

        El JWT es stateless (claim `sub`=user_id, sin `jti`); por eso se hace
        blacklist por user_id con TTL igual a la vida máxima del token. Toda
        petición posterior con ese token será rechazada en `get_current_user`.
        """
        user = await self._users.deactivate(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))
        await self._blacklist_user(user_id)
        logger.info("USER_SUSPENDED id=%s", user_id)
        return UserResponse.model_validate(user)

    async def reset_password(
        self, user_id: uuid.UUID, new_password: str
    ) -> UserResponse:
        """Restablece la contraseña de un usuario (SUPERADMIN).

        Invalida las sesiones activas del usuario vía blacklist para forzar el
        re-login con la nueva credencial.
        """
        user = await self._users.set_password(user_id, hash_password(new_password))
        if user is None:
            raise UserNotFoundError(str(user_id))
        await self._bump_session_epoch(user_id)
        logger.info("USER_PASSWORD_RESET id=%s", user_id)
        return UserResponse.model_validate(user)

    async def update_own_profile(
        self, user_id: uuid.UUID, full_name: str
    ) -> UserResponse:
        """Self-service: el usuario actualiza su propio nombre."""
        user = await self._users.update_profile(user_id, full_name=full_name)
        if user is None:
            raise UserNotFoundError(str(user_id))
        return UserResponse.model_validate(user)

    async def change_own_password(
        self, user_id: uuid.UUID, current_password: str, new_password: str
    ) -> UserResponse:
        """Self-service: cambia la propia clave verificando la actual.

        No invalida la sesión en curso (el usuario ya probó conocer la clave
        vigente); las demás sesiones siguen válidas hasta expirar por su TTL.
        """
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsError()
        updated = await self._users.set_password(user_id, hash_password(new_password))
        logger.info("USER_SELF_PASSWORD_CHANGE id=%s", user_id)
        return UserResponse.model_validate(updated)

    async def update_avatar(
        self, user_id: uuid.UUID, avatar_url: str
    ) -> UserResponse:
        """Actualiza la URL del avatar y borra del disco la foto que reemplaza."""
        previous = await self._users.get_by_id(user_id)
        if previous is None:
            raise UserNotFoundError(str(user_id))
        old_url = previous.avatar_url

        user = await self._users.set_avatar(user_id, avatar_url)
        if old_url and old_url != avatar_url:
            delete_static_file(old_url)

        logger.info("USER_AVATAR_UPDATED id=%s url=%s", user_id, avatar_url)
        return UserResponse.model_validate(user)

    async def clear_avatar(self, user_id: uuid.UUID) -> UserResponse:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))
        old_url = user.avatar_url

        updated = await self._users.set_avatar(user_id, None)
        if old_url:
            delete_static_file(old_url)

        logger.info("USER_AVATAR_CLEARED id=%s", user_id)
        return UserResponse.model_validate(updated)

    async def reactivate(self, user_id: uuid.UUID) -> UserResponse:
        user = await self._users.set_active(user_id, True)
        if user is None:
            raise UserNotFoundError(str(user_id))
        try:
            await self._redis.delete(
                token_blacklist_key(str(user_id)),
                token_valid_from_key(str(user_id)),
            )
        except RedisError as exc:
            logger.warning("REDIS_UNAVAILABLE unblacklist err=%s", exc)
        logger.info("USER_REACTIVATED id=%s", user_id)
        return UserResponse.model_validate(user)

    async def get_audit_log(
        self, user_id: uuid.UUID, page: int = 1, limit: int = 20
    ) -> UserAuditLogResponse:
        """HU-10-03: historial consolidado de mutaciones de un usuario.

        La paginación se aplica en memoria: las entradas se funden desde tres
        tablas distintas, así que el orden global solo existe una vez unidas.
        """
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))

        entries: list[AuditLogEntry] = []

        for cat in await self._categories.list_by_creator(user_id):
            entries.append(AuditLogEntry(
                action_type="CATEGORY_CREATED",
                entity_id=cat.id,
                summary=f"Categoría creada: {cat.name}",
                timestamp=cat.created_at,
            ))
        for loc in await self._locations.list_by_creator(user_id):
            entries.append(AuditLogEntry(
                action_type="LOCATION_CREATED",
                entity_id=loc.id,
                summary=f"Ubicación registrada: {loc.code}",
                timestamp=loc.created_at,
            ))
        for mov, supply_name, unit in await self._movements.list_by_performer_with_context(
            user_id
        ):
            verb = _MOVEMENT_VERB.get(mov.movement_type, mov.movement_type.value)
            unit_abbr = _UNIT_ABBR.get(unit, "")
            summary = f"{verb} de {_fmt_qty(mov.quantity)} {unit_abbr} de {supply_name}".strip()
            reason = _clean_reason(mov.notes)
            if reason:
                summary += f" · {reason}"
            entries.append(AuditLogEntry(
                action_type=f"MOVEMENT_{mov.movement_type.value}",
                entity_id=mov.id,
                summary=summary,
                timestamp=mov.created_at,
            ))

        entries.sort(key=lambda e: e.timestamp, reverse=True)
        offset = (page - 1) * limit
        return UserAuditLogResponse(
            user_id=user_id,
            email=user.email,
            total=len(entries),
            entries=entries[offset : offset + limit],
            page=page,
            limit=limit,
        )

    async def _blacklist_user(self, user_id: uuid.UUID) -> None:
        try:
            await self._redis.set(
                token_blacklist_key(str(user_id)),
                "1",
                ex=self._settings.access_token_expire_minutes * 60,
            )
        except RedisError as exc:
            logger.warning("REDIS_UNAVAILABLE blacklist err=%s", exc)

    async def _bump_session_epoch(self, user_id: uuid.UUID) -> None:
        """Marca 'ahora' como frontera: los tokens con iat anterior quedan inválidos.

        A diferencia de la blacklist de suspensión, permite el re-login inmediato
        porque el token nuevo tendrá iat posterior a esta marca.
        """
        import time
        try:
            await self._redis.set(
                token_valid_from_key(str(user_id)),
                str(int(time.time())),
                ex=self._settings.access_token_expire_minutes * 60,
            )
        except RedisError as exc:
            logger.warning("REDIS_UNAVAILABLE session_epoch err=%s", exc)
