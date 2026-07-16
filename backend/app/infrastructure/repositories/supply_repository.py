import uuid
from decimal import Decimal
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ItemType
from app.infrastructure.database.models.supply_model import SupplyItemModel


class SupplyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, item_id: uuid.UUID) -> SupplyItemModel | None:
        stmt = select(SupplyItemModel).where(SupplyItemModel.id == item_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, item_id: uuid.UUID) -> SupplyItemModel | None:
        """SELECT ... FOR UPDATE — lock a nivel de fila para operaciones de stock."""
        stmt = (
            select(SupplyItemModel)
            .where(SupplyItemModel.id == item_id, SupplyItemModel.is_active == True)  # noqa: E712
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> SupplyItemModel | None:
        stmt = select(SupplyItemModel).where(SupplyItemModel.sku == sku.upper())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def _active_filter(
        self,
        category_id: uuid.UUID | None,
        location_id: uuid.UUID | None,
        item_type: ItemType | None = None,
    ):
        stmt = select(SupplyItemModel).where(SupplyItemModel.is_active == True)  # noqa: E712
        if category_id:
            stmt = stmt.where(SupplyItemModel.category_id == category_id)
        if location_id:
            stmt = stmt.where(SupplyItemModel.location_id == location_id)
        if item_type is not None:
            stmt = stmt.where(SupplyItemModel.item_type == item_type)
        return stmt

    async def list_active(
        self,
        category_id: uuid.UUID | None = None,
        location_id: uuid.UUID | None = None,
        limit: int | None = None,
        offset: int = 0,
        item_type: ItemType | None = None,
    ) -> list[SupplyItemModel]:
        stmt = self._active_filter(category_id, location_id, item_type).order_by(
            SupplyItemModel.name
        )
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_active(
        self,
        category_id: uuid.UUID | None = None,
        location_id: uuid.UUID | None = None,
        item_type: ItemType | None = None,
    ) -> int:
        base = self._active_filter(category_id, location_id, item_type).subquery()
        stmt = select(func.count()).select_from(base)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def list_below_minimum(self) -> list[SupplyItemModel]:
        stmt = select(SupplyItemModel).where(
            SupplyItemModel.is_active == True,  # noqa: E712
            SupplyItemModel.current_stock < SupplyItemModel.minimum_stock,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: object) -> SupplyItemModel:
        if "sku" in kwargs and isinstance(kwargs["sku"], str):
            kwargs["sku"] = kwargs["sku"].upper()
        item = SupplyItemModel(**kwargs)
        self._session.add(item)
        await self._session.flush()
        await self._session.refresh(item)
        return item

    async def update_stock(self, item_id: uuid.UUID, new_stock: Decimal) -> SupplyItemModel:
        stmt = (
            update(SupplyItemModel)
            .where(SupplyItemModel.id == item_id)
            .values(current_stock=new_stock, updated_at=func.now())
            .returning(SupplyItemModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def deactivate(self, item_id: uuid.UUID) -> SupplyItemModel | None:
        stmt = (
            update(SupplyItemModel)
            .where(SupplyItemModel.id == item_id)
            .values(is_active=False)
            .returning(SupplyItemModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
