import logging
import uuid
from decimal import Decimal

from redis.asyncio import Redis

from app.application.schemas.movement_schema import (
    MovementCreate,
    MovementHistoryItem,
    MovementHistoryListResponse,
    MovementResponse,
    ReconciliationResponse,
)
from app.application.schemas.supply_schema import (
    SupplyItemCreate,
    SupplyItemListResponse,
    SupplyItemResponse,
)
from app.application.services.alert_service import AlertService
from app.domain.enums import ALLOWED_MOVEMENTS_BY_ROLE, ItemType, MovementType, UserRole
from app.domain.exceptions import (
    InsufficientStockError,
    ItemNotFoundError,
    MovementTypeNotAllowedError,
)
from app.infrastructure.cache.cache_keys import (
    SUPPLIES_PAGE_PATTERN,
    stock_lock_key,
    supplies_page_key,
)
from app.infrastructure.cache.redis_client import acquire_lock, cache_get, cache_set
from app.infrastructure.repositories.movement_repository import MovementRepository
from app.infrastructure.repositories.supply_repository import SupplyRepository

logger = logging.getLogger(__name__)


class SupplyService:
    def __init__(
        self,
        supply_repo: SupplyRepository,
        movement_repo: MovementRepository,
        alert_service: AlertService,
        redis: Redis,
    ) -> None:
        self._supply_repo = supply_repo
        self._movement_repo = movement_repo
        self._alert_service = alert_service
        self._redis = redis

    async def register_movement(
        self,
        data: MovementCreate,
        performed_by_id: uuid.UUID,
        user_role: UserRole,
    ) -> MovementResponse:
        # ── 1. RBAC: validar que el rol puede hacer este tipo de movimiento ──
        allowed = ALLOWED_MOVEMENTS_BY_ROLE.get(user_role, set())
        if data.movement_type not in allowed:
            raise MovementTypeNotAllowedError(
                movement_type=data.movement_type.value,
                allowed=[m.value for m in allowed],
            )

        # ── 2. Verificar que el insumo existe y está activo ──────────────────
        item = await self._supply_repo.get_by_id(data.supply_item_id)
        if item is None or not item.is_active:
            raise ItemNotFoundError(str(data.supply_item_id))

        # ── 3. Calcular nuevo stock según el tipo de movimiento ──────────────
        new_stock = self._calculate_new_stock(
            current=item.current_stock,
            quantity=data.quantity,
            movement_type=data.movement_type,
            item_name=item.name,
        )

        alert_needed = new_stock < item.minimum_stock

        # ── 4. Lock distribuido Redis + SELECT FOR UPDATE en PostgreSQL ───────
        lock_key = stock_lock_key(str(data.supply_item_id))
        async with acquire_lock(self._redis, lock_key, timeout_seconds=5):
            # Re-lectura con lock para garantizar consistencia bajo concurrencia
            locked_item = await self._supply_repo.get_by_id_for_update(data.supply_item_id)
            if locked_item is None:
                raise ItemNotFoundError(str(data.supply_item_id))

            # Segunda validación con el stock más reciente (puede haber cambiado)
            new_stock = self._calculate_new_stock(
                current=locked_item.current_stock,
                quantity=data.quantity,
                movement_type=data.movement_type,
                item_name=locked_item.name,
            )
            stock_before = locked_item.current_stock
            alert_needed = new_stock < locked_item.minimum_stock

            await self._supply_repo.update_stock(data.supply_item_id, new_stock)

            movement = await self._movement_repo.create(
                supply_item_id=data.supply_item_id,
                movement_type=data.movement_type,
                quantity=data.quantity,
                stock_before=stock_before,
                stock_after=new_stock,
                notes=data.notes,
                alert_triggered=alert_needed,
                performed_by=performed_by_id,
            )

        # El stock cambió → invalidar el índice paginado cacheado (HU-06).
        await self._invalidate_supplies_cache()

        # ── 5. Publicar alerta fuera del lock (no bloquea la respuesta) ───────
        if alert_needed:
            await self._alert_service.publish_low_stock(
                supply_item_id=data.supply_item_id,
                supply_name=locked_item.name,
                current_stock=new_stock,
                minimum_stock=locked_item.minimum_stock,
            )

        logger.info(
            "MOVEMENT_REGISTERED type=%s item=%s before=%s after=%s alert=%s",
            data.movement_type, data.supply_item_id, stock_before, new_stock, alert_needed,
        )
        return MovementResponse.model_validate(movement)

    async def list_active(
        self,
        category_id: uuid.UUID | None = None,
        location_id: uuid.UUID | None = None,
        page: int = 1,
        limit: int = 20,
        item_type: ItemType | None = None,
    ) -> tuple[SupplyItemListResponse, str]:
        """HU-06: listado paginado cache-first.

        Devuelve (respuesta, cache_status) donde cache_status ∈ {"HIT", "MISS"}.
        offset = (page - 1) * limit. `item_type` separa insumos de productos (HU-17).
        """
        cache_key = supplies_page_key(
            page, limit,
            str(category_id) if category_id else None,
            str(location_id) if location_id else None,
            item_type.value if item_type else None,
        )
        cached = await cache_get(self._redis, cache_key)
        if cached is not None:
            return SupplyItemListResponse(**cached), "HIT"

        offset = (page - 1) * limit
        items = await self._supply_repo.list_active(
            category_id, location_id, limit=limit, offset=offset, item_type=item_type
        )
        total = await self._supply_repo.count_active(
            category_id, location_id, item_type=item_type
        )
        responses = [SupplyItemResponse.model_validate(i) for i in items]
        low_stock_count = sum(1 for r in responses if r.is_below_minimum)
        payload = SupplyItemListResponse(
            items=responses,
            total=total,
            low_stock_count=low_stock_count,
            page=page,
            limit=limit,
        )
        await cache_set(self._redis, cache_key, payload.model_dump())
        return payload, "MISS"

    async def get_detail(self, supply_id: uuid.UUID) -> SupplyItemResponse:
        """HU-06: detalle de un insumo por id.

        No exige que esté activo: la ficha debe poder consultarse también para
        insumos dados de baja (coherente con `list_movements`).
        """
        item = await self._supply_repo.get_by_id(supply_id)
        if item is None:
            raise ItemNotFoundError(str(supply_id))
        return SupplyItemResponse.model_validate(item)

    async def _invalidate_supplies_cache(self) -> None:
        """Elimina todas las páginas cacheadas de insumos tras una mutación (HU-06-02)."""
        try:
            keys = [k async for k in self._redis.scan_iter(match=SUPPLIES_PAGE_PATTERN)]
            if keys:
                await self._redis.delete(*keys)
        except Exception as exc:  # noqa: BLE001
            logger.warning("REDIS_UNAVAILABLE invalidate_supplies err=%s", exc)

    async def reconcile(
        self,
        supply_id: uuid.UUID,
        physical_stock: Decimal,
        reason: str,
        performed_by_id: uuid.UUID,
    ) -> ReconciliationResponse:
        """HU-11: concilia el stock registrado con el conteo físico real.

        Δ = physical_stock − current_stock. Registra un movimiento ADJUSTMENT
        (ADD o SUB según el signo) preservando la inmutabilidad histórica y
        dispara alerta si el nuevo stock cae bajo el mínimo.

        La autorización (solo ADMIN+) se aplica en la capa de API (endpoint).
        """
        lock_key = stock_lock_key(str(supply_id))
        async with acquire_lock(self._redis, lock_key, timeout_seconds=5):
            item = await self._supply_repo.get_by_id_for_update(supply_id)
            if item is None:
                raise ItemNotFoundError(str(supply_id))

            stock_before = item.current_stock
            delta = physical_stock - stock_before
            alert_needed = physical_stock < item.minimum_stock

            movement_type = (
                MovementType.ADJUSTMENT_ADD if delta >= 0 else MovementType.ADJUSTMENT_SUB
            )

            await self._supply_repo.update_stock(supply_id, physical_stock)
            movement = await self._movement_repo.create(
                supply_item_id=supply_id,
                movement_type=movement_type,
                quantity=abs(delta),
                stock_before=stock_before,
                stock_after=physical_stock,
                notes=reason,
                alert_triggered=alert_needed,
                performed_by=performed_by_id,
            )
            item_name = item.name
            minimum = item.minimum_stock

        await self._invalidate_supplies_cache()

        if alert_needed:
            await self._alert_service.publish_low_stock(
                supply_item_id=supply_id,
                supply_name=item_name,
                current_stock=physical_stock,
                minimum_stock=minimum,
            )

        logger.info(
            "RECONCILIATION supply=%s delta=%s before=%s after=%s alert=%s",
            supply_id, delta, stock_before, physical_stock, alert_needed,
        )
        return ReconciliationResponse(
            audit_id=movement.id,
            supply_id=supply_id,
            delta=delta,
            stock_before=stock_before,
            stock_after=physical_stock,
            alert_triggered=alert_needed,
        )

    async def list_movements(
        self,
        supply_id: uuid.UUID,
        page: int = 1,
        limit: int = 50,
    ) -> MovementHistoryListResponse:
        """HU-07: historial de movimientos de un insumo con trazabilidad.

        No exige que el insumo esté activo: la auditoría debe poder consultarse
        también para insumos dados de baja.
        """
        item = await self._supply_repo.get_by_id(supply_id)
        if item is None:
            raise ItemNotFoundError(str(supply_id))

        offset = (page - 1) * limit
        rows = await self._movement_repo.list_by_supply_item_with_user(
            supply_id, limit=limit, offset=offset
        )
        total = await self._movement_repo.count_by_supply_item(supply_id)

        items = [self._to_history_item(movement, email) for movement, email in rows]
        return MovementHistoryListResponse(
            items=items, total=total, page=page, limit=limit
        )

    @staticmethod
    def _to_history_item(movement: object, user_email: str) -> MovementHistoryItem:
        is_adjustment = movement.movement_type in (
            MovementType.ADJUSTMENT_ADD,
            MovementType.ADJUSTMENT_SUB,
        )
        return MovementHistoryItem(
            movement_id=movement.id,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            stock_before=movement.stock_before,
            stock_after=movement.stock_after,
            executed_by_user_id=movement.performed_by,
            user_email=user_email,
            is_adjustment=is_adjustment,
            # El modelo no tiene columna dedicada: cuando es un ajuste, la razón
            # se registra en `notes`.
            adjustment_reason=movement.notes if is_adjustment else None,
            notes=movement.notes,
            alert_triggered=movement.alert_triggered,
            created_at=movement.created_at,
        )

    async def create(
        self, data: SupplyItemCreate, created_by_id: uuid.UUID
    ) -> SupplyItemResponse:
        item = await self._supply_repo.create(
            **data.model_dump(),
            created_by=created_by_id,
        )
        # HU-06-02: una inserción invalida el índice paginado en Redis.
        await self._invalidate_supplies_cache()
        return SupplyItemResponse.model_validate(item)

    def _calculate_new_stock(
        self,
        current: Decimal,
        quantity: Decimal,
        movement_type: object,
        item_name: str,
    ) -> Decimal:
        from app.domain.enums import MovementType
        if movement_type in (MovementType.EXIT, MovementType.WASTE, MovementType.ADJUSTMENT_SUB):
            new_stock = current - quantity
            if new_stock < 0:
                raise InsufficientStockError(
                    available=current, requested=quantity, item_name=item_name
                )
            return new_stock
        # ENTRY, ADJUSTMENT_ADD, TRANSFER
        return current + quantity
