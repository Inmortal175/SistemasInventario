import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.location_model import LocationModel


class LocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, location_id: uuid.UUID) -> LocationModel | None:
        stmt = select(LocationModel).where(LocationModel.id == location_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> LocationModel | None:
        stmt = select(LocationModel).where(
            LocationModel.code == code.upper(),
            LocationModel.is_active == True,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[LocationModel]:
        stmt = (
            select(LocationModel)
            .where(LocationModel.is_active == True)  # noqa: E712
            .order_by(LocationModel.code)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_creator(self, user_id: uuid.UUID) -> list[LocationModel]:
        stmt = (
            select(LocationModel)
            .where(LocationModel.created_by == user_id)
            .order_by(LocationModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: object) -> LocationModel:
        location = LocationModel(**kwargs)
        self._session.add(location)
        await self._session.flush()
        await self._session.refresh(location)
        return location

    async def deactivate(self, location_id: uuid.UUID) -> LocationModel | None:
        stmt = (
            update(LocationModel)
            .where(LocationModel.id == location_id)
            .values(is_active=False)
            .returning(LocationModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
