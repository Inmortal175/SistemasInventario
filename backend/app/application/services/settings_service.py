import logging
import uuid

from pydantic import ValidationError
from redis.asyncio import Redis

from app.application.schemas.settings_schema import SettingsResponse, SettingsUpdate
from app.core.uploads import delete_static_file
from app.domain.enums import LoginBackgroundDevice
from app.infrastructure.cache.cache_keys import SYSTEM_SETTINGS_KEY
from app.infrastructure.cache.redis_client import cache_delete, cache_get, cache_set
from app.infrastructure.repositories.interfaces.i_settings_repo import (
    ISettingsRepository,
)

logger = logging.getLogger(__name__)


def _background_field(device: LoginBackgroundDevice) -> str:
    return f"login_bg_{device.value}_url"


class SettingsService:
    """Identidad visual del sistema: nombre, logo del login y paleta de color."""

    def __init__(self, repo: ISettingsRepository, redis: Redis) -> None:
        self._repo = repo
        self._redis = redis

    async def get(self) -> SettingsResponse:
        cached = await cache_get(self._redis, SYSTEM_SETTINGS_KEY)
        if cached is not None:
            try:
                return SettingsResponse(**cached)
            except ValidationError:
                # Entrada escrita por una versión anterior del schema: tras un
                # deploy que agrega campos, la caché vieja no debe tumbar la API.
                logger.warning("SETTINGS_CACHE_STALE key=%s", SYSTEM_SETTINGS_KEY)
                await cache_delete(self._redis, SYSTEM_SETTINGS_KEY)

        settings = await self._repo.get()
        response = SettingsResponse.model_validate(settings)
        await cache_set(self._redis, SYSTEM_SETTINGS_KEY, response.model_dump(mode="json"))
        return response

    async def update(
        self, data: SettingsUpdate, updated_by: uuid.UUID
    ) -> SettingsResponse:
        fields = data.model_dump(exclude_none=True)
        if "theme" in fields:
            fields["theme"] = data.theme.value

        # Los campos de texto libre (RUC, dirección…) se borran mandando "".
        # `update` trata None como «no tocar», así que el vaciado va por `clear`.
        blanks = [key for key, value in fields.items() if value == ""]
        for key in blanks:
            fields.pop(key)

        settings = await self._repo.update(updated_by=updated_by, **fields)
        if blanks:
            settings = await self._repo.clear(updated_by, *blanks)

        logger.info("SETTINGS_UPDATED by=%s fields=%s", updated_by, sorted(fields))
        return await self._refresh_cache(settings)

    async def set_logo(self, logo_url: str, updated_by: uuid.UUID) -> SettingsResponse:
        return await self._replace_image(updated_by, "logo_url", logo_url)

    async def clear_logo(self, updated_by: uuid.UUID) -> SettingsResponse:
        return await self._replace_image(updated_by, "logo_url", None)

    async def set_login_background(
        self, device: LoginBackgroundDevice, url: str, updated_by: uuid.UUID
    ) -> SettingsResponse:
        return await self._replace_image(updated_by, _background_field(device), url)

    async def clear_login_background(
        self, device: LoginBackgroundDevice, updated_by: uuid.UUID
    ) -> SettingsResponse:
        return await self._replace_image(updated_by, _background_field(device), None)

    async def _replace_image(
        self, updated_by: uuid.UUID, field: str, url: str | None
    ) -> SettingsResponse:
        """Apunta `field` a la nueva imagen y borra del disco la que reemplaza."""
        current = await self._repo.get()
        previous = getattr(current, field)

        if url is None:
            settings = await self._repo.clear(updated_by, field)
        else:
            settings = await self._repo.update(updated_by=updated_by, **{field: url})

        if previous and previous != url:
            delete_static_file(previous)

        logger.info(
            "SETTINGS_IMAGE_SET by=%s field=%s url=%s previous=%s",
            updated_by, field, url, previous,
        )
        return await self._refresh_cache(settings)

    async def _refresh_cache(self, settings: object) -> SettingsResponse:
        await cache_delete(self._redis, SYSTEM_SETTINGS_KEY)
        response = SettingsResponse.model_validate(settings)
        await cache_set(self._redis, SYSTEM_SETTINGS_KEY, response.model_dump(mode="json"))
        return response
