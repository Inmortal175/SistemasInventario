"""Interfaz del repositorio de historial de movimientos — principio DIP."""
import uuid
from typing import Protocol

from app.infrastructure.database.models.movement_model import MovementHistoryModel


class IMovementRepository(Protocol):
    async def create(self, **kwargs: object) -> MovementHistoryModel: ...
    async def get_by_supply_item(
        self,
        supply_item_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MovementHistoryModel]: ...
    async def list_by_supply_item_with_user(
        self,
        supply_item_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[MovementHistoryModel, str]]: ...
    async def count_by_supply_item(self, supply_item_id: uuid.UUID) -> int: ...
    async def get_by_id(self, movement_id: uuid.UUID) -> MovementHistoryModel | None: ...
