import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.production_model import (
    ProductionRunItemModel,
    ProductionRunModel,
)
from app.infrastructure.database.models.recipe_model import RecipeModel
from app.infrastructure.database.models.supply_model import SupplyItemModel
from app.infrastructure.database.models.user_model import UserModel


class ProductionRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs: object) -> ProductionRunModel:
        run = ProductionRunModel(**kwargs)
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def add_item(self, **kwargs: object) -> ProductionRunItemModel:
        """Asienta un insumo consumido (snapshot de la lista de preparación)."""
        item = ProductionRunItemModel(**kwargs)
        self._session.add(item)
        await self._session.flush()
        return item

    async def list_items(
        self, production_run_id: uuid.UUID
    ) -> list[ProductionRunItemModel]:
        """Insumos consumidos por una corrida, en el orden en que se asentaron."""
        stmt = (
            select(ProductionRunItemModel)
            .where(ProductionRunItemModel.production_run_id == production_run_id)
            .order_by(ProductionRunItemModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_context(self, production_id: uuid.UUID) -> dict | None:
        """Cabecera de una corrida (receta, producto, cantidad, ejecutor, fecha)."""
        stmt = (
            select(
                ProductionRunModel.id.label("production_id"),
                RecipeModel.name.label("recipe_name"),
                SupplyItemModel.name.label("product_name"),
                ProductionRunModel.quantity_produced.label("quantity_produced"),
                ProductionRunModel.total_ingredient_cost.label("total_ingredient_cost"),
                UserModel.email.label("performed_by_email"),
                ProductionRunModel.created_at.label("created_at"),
            )
            .join(RecipeModel, ProductionRunModel.recipe_id == RecipeModel.id)
            .join(UserModel, ProductionRunModel.performed_by == UserModel.id)
            .outerjoin(
                SupplyItemModel,
                ProductionRunModel.product_supply_item_id == SupplyItemModel.id,
            )
            .where(ProductionRunModel.id == production_id)
        )
        result = await self._session.execute(stmt)
        row = result.first()
        return dict(row._mapping) if row else None

    async def list_with_context(
        self, limit: int = 20, offset: int = 0
    ) -> list[dict]:
        """Historial desc por fecha con nombre de receta, producto y email del ejecutor.

        Devuelve dicts planos para evitar lazy-loads en contexto async. El LEFT JOIN
        del producto cubre las corridas de recetas que no generan stock trazable.
        """
        stmt = (
            select(
                ProductionRunModel.id.label("production_id"),
                ProductionRunModel.recipe_id.label("recipe_id"),
                RecipeModel.name.label("recipe_name"),
                ProductionRunModel.product_supply_item_id.label("product_supply_item_id"),
                SupplyItemModel.name.label("product_name"),
                ProductionRunModel.quantity_produced.label("quantity_produced"),
                ProductionRunModel.total_ingredient_cost.label("total_ingredient_cost"),
                UserModel.email.label("performed_by_email"),
                ProductionRunModel.created_at.label("created_at"),
            )
            .join(RecipeModel, ProductionRunModel.recipe_id == RecipeModel.id)
            .join(UserModel, ProductionRunModel.performed_by == UserModel.id)
            .outerjoin(
                SupplyItemModel,
                ProductionRunModel.product_supply_item_id == SupplyItemModel.id,
            )
            .order_by(ProductionRunModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]

    async def count(self) -> int:
        stmt = select(func.count()).select_from(ProductionRunModel)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
