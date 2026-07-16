"""Interfaz del repositorio de ajustes del sistema — principio DIP."""
import uuid
from typing import Protocol

from app.infrastructure.database.models.settings_model import SystemSettingsModel


class ISettingsRepository(Protocol):
    async def get(self) -> SystemSettingsModel: ...
    async def update(
        self, updated_by: uuid.UUID, **fields: object
    ) -> SystemSettingsModel: ...
    async def clear(
        self, updated_by: uuid.UUID, *fields: str
    ) -> SystemSettingsModel: ...
