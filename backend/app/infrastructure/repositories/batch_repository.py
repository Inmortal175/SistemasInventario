import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.batch_model import SupplyBatchModel


class BatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs: object) -> SupplyBatchModel:
        batch = SupplyBatchModel(**kwargs)
        self._session.add(batch)
        await self._session.flush()
        await self._session.refresh(batch)
        return batch

    async def get_by_id(self, batch_id: uuid.UUID) -> SupplyBatchModel | None:
        stmt = select(SupplyBatchModel).where(SupplyBatchModel.id == batch_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_fifo_for_update(
        self, supply_item_id: uuid.UUID
    ) -> list[SupplyBatchModel]:
        """Lotes activos con stock, ordenados FIFO (vencimiento asc, luego antigüedad).

        Bloquea las filas (FOR UPDATE) para el descuento atómico por lotes.
        Los NULLs de expiration_date van al final (se consumen después).
        """
        stmt = (
            select(SupplyBatchModel)
            .where(
                SupplyBatchModel.supply_item_id == supply_item_id,
                SupplyBatchModel.is_active == True,  # noqa: E712
                SupplyBatchModel.current_stock > 0,
            )
            .order_by(
                SupplyBatchModel.expiration_date.asc().nulls_last(),
                SupplyBatchModel.created_at.asc(),
            )
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active_fifo(
        self, supply_item_id: uuid.UUID
    ) -> list[SupplyBatchModel]:
        """Lotes activos con stock en orden FIFO, SIN bloquear filas (solo lectura).

        Mismo orden que `list_active_fifo_for_update` pero para previsualizar el
        consumo (lista de preparación del simulacro), sin adquirir locks.
        """
        stmt = (
            select(SupplyBatchModel)
            .where(
                SupplyBatchModel.supply_item_id == supply_item_id,
                SupplyBatchModel.is_active == True,  # noqa: E712
                SupplyBatchModel.current_stock > 0,
            )
            .order_by(
                SupplyBatchModel.expiration_date.asc().nulls_last(),
                SupplyBatchModel.created_at.asc(),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active_by_supply(
        self, supply_item_id: uuid.UUID
    ) -> list[SupplyBatchModel]:
        stmt = (
            select(SupplyBatchModel)
            .where(
                SupplyBatchModel.supply_item_id == supply_item_id,
                SupplyBatchModel.is_active == True,  # noqa: E712
            )
            .order_by(SupplyBatchModel.expiration_date.asc().nulls_last())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def sum_active_stock(self, supply_item_id: uuid.UUID) -> Decimal:
        stmt = select(func.coalesce(func.sum(SupplyBatchModel.current_stock), 0)).where(
            SupplyBatchModel.supply_item_id == supply_item_id,
            SupplyBatchModel.is_active == True,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return Decimal(str(result.scalar_one()))

    async def apply_consumption(
        self, batch_id: uuid.UUID, new_stock: Decimal
    ) -> None:
        """Actualiza el stock de un lote; lo desactiva si queda en cero."""
        stmt = (
            update(SupplyBatchModel)
            .where(SupplyBatchModel.id == batch_id)
            .values(current_stock=new_stock, is_active=(new_stock > 0))
        )
        await self._session.execute(stmt)

    async def list_expiring(self, threshold: date) -> list[SupplyBatchModel]:
        """Lotes activos, no alertados, que vencen en o antes de `threshold` (HU-13-03)."""
        stmt = (
            select(SupplyBatchModel)
            .where(
                SupplyBatchModel.is_active == True,  # noqa: E712
                SupplyBatchModel.alert_sent == False,  # noqa: E712
                SupplyBatchModel.expiration_date.isnot(None),
                SupplyBatchModel.expiration_date <= threshold,
            )
            .order_by(SupplyBatchModel.expiration_date.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_alert_sent(self, batch_id: uuid.UUID) -> None:
        stmt = (
            update(SupplyBatchModel)
            .where(SupplyBatchModel.id == batch_id)
            .values(alert_sent=True)
        )
        await self._session.execute(stmt)

    async def financial_active_batches(self) -> list[SupplyBatchModel]:
        """Todos los lotes activos con stock — para la valorización (HU-16-02)."""
        stmt = select(SupplyBatchModel).where(
            SupplyBatchModel.is_active == True,  # noqa: E712
            SupplyBatchModel.current_stock > 0,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
