import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.user_model import UserModel


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[UserModel]:
        stmt = select(UserModel).where(UserModel.is_active == True).order_by(UserModel.created_at)  # noqa: E712
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[UserModel]:
        """Incluye suspendidos: sin ellos el SUPERADMIN no podría reactivarlos."""
        stmt = select(UserModel).order_by(UserModel.created_at)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: object) -> UserModel:
        if "email" in kwargs and isinstance(kwargs["email"], str):
            kwargs["email"] = kwargs["email"].lower()
        user = UserModel(**kwargs)
        self._session.add(user)
        await self._session.flush()   # obtiene el ID sin hacer commit aún
        await self._session.refresh(user)
        return user

    async def deactivate(self, user_id: uuid.UUID) -> UserModel | None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_active=False)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_active(self, user_id: uuid.UUID, active: bool) -> UserModel | None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_active=active)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_password(
        self, user_id: uuid.UUID, hashed_password: str
    ) -> UserModel | None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(hashed_password=hashed_password)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_profile(self, user_id: uuid.UUID, **fields: object) -> UserModel | None:
        clean = {k: v for k, v in fields.items() if v is not None}
        if not clean:
            return await self.get_by_id(user_id)
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(**clean)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_avatar(self, user_id: uuid.UUID, avatar_url: str | None) -> UserModel | None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(avatar_url=avatar_url)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
