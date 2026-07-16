import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.settings_model import (
    SETTINGS_ID,
    SystemSettingsModel,
)


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> SystemSettingsModel:
        """Devuelve la fila única, creándola con los valores por defecto si la
        migración corrió antes de que existiera (o si alguien la borró a mano)."""
        stmt = select(SystemSettingsModel).where(SystemSettingsModel.id == SETTINGS_ID)
        settings = (await self._session.execute(stmt)).scalar_one_or_none()
        if settings is None:
            settings = SystemSettingsModel(id=SETTINGS_ID)
            self._session.add(settings)
            await self._session.flush()
            await self._session.refresh(settings)
        return settings

    async def update(
        self, updated_by: uuid.UUID, **fields: object
    ) -> SystemSettingsModel:
        """Los None se ignoran: representan «no tocar este campo»."""
        settings = await self.get()
        for key, value in fields.items():
            if value is not None:
                setattr(settings, key, value)
        settings.updated_by = updated_by
        await self._session.flush()
        await self._session.refresh(settings)
        return settings

    async def clear(self, updated_by: uuid.UUID, *fields: str) -> SystemSettingsModel:
        """Pone campos a NULL. `update` no sirve: allí un None significa
        «no tocar», así que el borrado necesita su propio camino."""
        settings = await self.get()
        for field in fields:
            setattr(settings, field, None)
        settings.updated_by = updated_by
        await self._session.flush()
        await self._session.refresh(settings)
        return settings
