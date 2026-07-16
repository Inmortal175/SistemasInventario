import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.category_model import CategoryModel


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, category_id: uuid.UUID) -> CategoryModel | None:
        stmt = select(CategoryModel).where(CategoryModel.id == category_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> CategoryModel | None:
        stmt = select(CategoryModel).where(
            CategoryModel.slug == slug,
            CategoryModel.is_active == True,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> CategoryModel | None:
        stmt = select(CategoryModel).where(
            CategoryModel.name == name,
            CategoryModel.is_active == True,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[CategoryModel]:
        stmt = (
            select(CategoryModel)
            .where(CategoryModel.is_active == True)  # noqa: E712
            .order_by(CategoryModel.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_creator(self, user_id: uuid.UUID) -> list[CategoryModel]:
        stmt = (
            select(CategoryModel)
            .where(CategoryModel.created_by == user_id)
            .order_by(CategoryModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: object) -> CategoryModel:
        category = CategoryModel(**kwargs)
        self._session.add(category)
        await self._session.flush()
        await self._session.refresh(category)
        return category

    async def deactivate(self, category_id: uuid.UUID) -> CategoryModel | None:
        stmt = (
            update(CategoryModel)
            .where(CategoryModel.id == category_id)
            .values(is_active=False)
            .returning(CategoryModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
