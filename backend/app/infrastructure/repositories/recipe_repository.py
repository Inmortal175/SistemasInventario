import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.recipe_model import RecipeItemModel, RecipeModel


class RecipeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs: object) -> RecipeModel:
        recipe = RecipeModel(**kwargs)
        self._session.add(recipe)
        await self._session.flush()
        await self._session.refresh(recipe)
        return recipe

    async def add_item(self, **kwargs: object) -> RecipeItemModel:
        item = RecipeItemModel(**kwargs)
        self._session.add(item)
        await self._session.flush()
        return item

    async def get_with_items(self, recipe_id: uuid.UUID) -> RecipeModel | None:
        stmt = (
            select(RecipeModel)
            .where(RecipeModel.id == recipe_id, RecipeModel.is_active == True)  # noqa: E712
            .options(selectinload(RecipeModel.items))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> RecipeModel | None:
        stmt = select(RecipeModel).where(RecipeModel.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[RecipeModel]:
        stmt = (
            select(RecipeModel)
            .where(RecipeModel.is_active == True)  # noqa: E712
            .options(selectinload(RecipeModel.items))
            .order_by(RecipeModel.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
