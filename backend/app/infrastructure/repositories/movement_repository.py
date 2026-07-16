import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import MovementType
from app.infrastructure.database.models.movement_model import MovementHistoryModel
from app.infrastructure.database.models.user_model import UserModel


class MovementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs: object) -> MovementHistoryModel:
        movement = MovementHistoryModel(**kwargs)
        self._session.add(movement)
        await self._session.flush()
        await self._session.refresh(movement)
        return movement

    async def get_by_id(self, movement_id: uuid.UUID) -> MovementHistoryModel | None:
        stmt = select(MovementHistoryModel).where(MovementHistoryModel.id == movement_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_supply_item(
        self,
        supply_item_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MovementHistoryModel]:
        stmt = (
            select(MovementHistoryModel)
            .where(MovementHistoryModel.supply_item_id == supply_item_id)
            .order_by(MovementHistoryModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_supply_item_with_user(
        self,
        supply_item_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[MovementHistoryModel, str]]:
        """HU-07: historial ordenado desc por timestamp, con el email del ejecutor.

        Devuelve tuplas (movimiento, email) para evitar un lazy-load de la
        relación `performer` (configurada como noload en contexto async).
        """
        stmt = (
            select(MovementHistoryModel, UserModel.email)
            .join(UserModel, MovementHistoryModel.performed_by == UserModel.id)
            .where(MovementHistoryModel.supply_item_id == supply_item_id)
            .order_by(MovementHistoryModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def sum_waste_cost(self, start_date: date | None = None) -> Decimal:
        """Σ (quantity × unit_cost) de los movimientos WASTE desde start_date (HU-16-02)."""
        stmt = select(
            func.coalesce(
                func.sum(MovementHistoryModel.quantity * MovementHistoryModel.unit_cost),
                0,
            )
        ).where(
            MovementHistoryModel.movement_type == MovementType.WASTE,
            MovementHistoryModel.unit_cost.isnot(None),
        )
        if start_date is not None:
            start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            stmt = stmt.where(MovementHistoryModel.created_at >= start_dt)
        result = await self._session.execute(stmt)
        return Decimal(str(result.scalar_one()))

    async def count_since(self, since: datetime) -> int:
        """Nº de movimientos registrados desde `since` (HU-08 KPIs)."""
        stmt = select(func.count()).select_from(MovementHistoryModel).where(
            MovementHistoryModel.created_at >= since
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def top_wasted_supplies(self, limit: int = 5) -> list[tuple[uuid.UUID, Decimal]]:
        """Insumos con mayor cantidad mermada (HU-08). Devuelve (supply_id, total)."""
        stmt = (
            select(
                MovementHistoryModel.supply_item_id,
                func.sum(MovementHistoryModel.quantity).label("total"),
            )
            .where(MovementHistoryModel.movement_type == MovementType.WASTE)
            .group_by(MovementHistoryModel.supply_item_id)
            .order_by(func.sum(MovementHistoryModel.quantity).desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [(row[0], Decimal(str(row[1]))) for row in result.all()]

    async def list_by_performer(
        self, user_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[MovementHistoryModel]:
        stmt = (
            select(MovementHistoryModel)
            .where(MovementHistoryModel.performed_by == user_id)
            .order_by(MovementHistoryModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_performer_with_context(
        self, user_id: uuid.UUID, limit: int = 200, offset: int = 0
    ) -> list[tuple[MovementHistoryModel, str, str]]:
        """Movimientos de un usuario con el nombre y la unidad del insumo.

        Devuelve tuplas (movimiento, supply_name, unit_of_measure) para construir
        un resumen de auditoría legible sin lazy-loads en contexto async.
        """
        from app.infrastructure.database.models.supply_model import SupplyItemModel

        stmt = (
            select(
                MovementHistoryModel,
                SupplyItemModel.name,
                SupplyItemModel.unit_of_measure,
            )
            .join(SupplyItemModel, MovementHistoryModel.supply_item_id == SupplyItemModel.id)
            .where(MovementHistoryModel.performed_by == user_id)
            .order_by(MovementHistoryModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def export_denormalized(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> list[dict]:
        """HU-12: vista de hechos plana (JOIN supplies+categories+locations+users).

        Aplana el esquema 3NF a un registro por movimiento, listo para ETL/OLAP.
        El rango es inclusivo en ambos extremos: `end_date` cubre el día entero.
        """
        from app.infrastructure.database.models.category_model import CategoryModel
        from app.infrastructure.database.models.location_model import LocationModel
        from app.infrastructure.database.models.supply_model import SupplyItemModel

        stmt = (
            select(
                MovementHistoryModel.id.label("movement_id"),
                MovementHistoryModel.created_at.label("timestamp"),
                UserModel.id.label("user_id"),
                UserModel.role.label("user_role"),
                UserModel.email.label("user_email"),
                SupplyItemModel.id.label("supply_id"),
                SupplyItemModel.name.label("supply_name"),
                SupplyItemModel.item_type.label("item_type"),
                CategoryModel.name.label("category_name"),
                LocationModel.code.label("location_code"),
                MovementHistoryModel.movement_type.label("movement_type"),
                MovementHistoryModel.quantity.label("quantity"),
                MovementHistoryModel.unit_cost.label("unit_cost"),
                MovementHistoryModel.stock_before.label("stock_before"),
                MovementHistoryModel.stock_after.label("stock_after"),
                MovementHistoryModel.notes.label("notes"),
            )
            .join(UserModel, MovementHistoryModel.performed_by == UserModel.id)
            .join(SupplyItemModel, MovementHistoryModel.supply_item_id == SupplyItemModel.id)
            .join(CategoryModel, SupplyItemModel.category_id == CategoryModel.id)
            .join(LocationModel, SupplyItemModel.location_id == LocationModel.id)
            .order_by(MovementHistoryModel.created_at.desc())
        )
        if start_date is not None:
            start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            stmt = stmt.where(MovementHistoryModel.created_at >= start_dt)
        if end_date is not None:
            # `time.max` incluye el último día completo; con `time.min` se perdería
            # todo lo registrado ese día después de medianoche.
            end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
            stmt = stmt.where(MovementHistoryModel.created_at <= end_dt)

        result = await self._session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]

    async def count_by_supply_item(self, supply_item_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(MovementHistoryModel)
            .where(MovementHistoryModel.supply_item_id == supply_item_id)
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
