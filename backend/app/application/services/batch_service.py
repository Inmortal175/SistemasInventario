import logging
import uuid
from datetime import date, timedelta
from decimal import Decimal

from redis.asyncio import Redis

from app.application.schemas.batch_schema import (
    BatchCreate,
    BatchCreateResult,
    BatchListResponse,
    BatchResponse,
    ConsumptionBreakdownItem,
    FifoConsumptionResponse,
    FinancialsResponse,
)
from app.application.services.alert_service import AlertService
from app.domain.enums import ALLOWED_MOVEMENTS_BY_ROLE, MovementType, UserRole
from app.domain.exceptions import (
    InsufficientStockError,
    ItemNotFoundError,
    MovementTypeNotAllowedError,
)
from app.infrastructure.cache.cache_keys import (
    ALERT_EXPIRATION_CHANNEL,
    SUPPLIES_PAGE_PATTERN,
    stock_lock_key,
)
from app.infrastructure.cache.redis_client import acquire_lock, cache_publish
from app.infrastructure.repositories.batch_repository import BatchRepository
from app.infrastructure.repositories.movement_repository import MovementRepository
from app.infrastructure.repositories.supply_repository import SupplyRepository

logger = logging.getLogger(__name__)


class BatchService:
    """HU-13 (lotes/FIFO), HU-16 (valorización) y HU-15 (soporte de producción)."""

    def __init__(
        self,
        supply_repo: SupplyRepository,
        batch_repo: BatchRepository,
        movement_repo: MovementRepository,
        alert_service: AlertService,
        redis: Redis,
    ) -> None:
        self._supply_repo = supply_repo
        self._batches = batch_repo
        self._movements = movement_repo
        self._alert = alert_service
        self._redis = redis

    async def create_batch(
        self,
        supply_id: uuid.UUID,
        data: BatchCreate,
        performed_by_id: uuid.UUID,
    ) -> BatchCreateResult:
        """HU-13-01 / HU-16-01: registra un lote y recalcula el stock total del insumo."""
        lock_key = stock_lock_key(str(supply_id))
        async with acquire_lock(self._redis, lock_key, timeout_seconds=5):
            item = await self._supply_repo.get_by_id_for_update(supply_id)
            if item is None:
                raise ItemNotFoundError(str(supply_id))

            stock_before = item.current_stock
            batch = await self._batches.create(
                supply_item_id=supply_id,
                batch_code=data.batch_code,
                initial_stock=data.quantity,
                current_stock=data.quantity,
                unit_cost=data.unit_cost,
                vendor_name=data.vendor_name,
                expiration_date=data.expiration_date,
                is_active=True,
            )

            # current_stock del insumo = Σ stock_actual de lotes activos
            new_total = await self._batches.sum_active_stock(supply_id)
            await self._supply_repo.update_stock(supply_id, new_total)

            total_cost = data.quantity * data.unit_cost
            movement = await self._movements.create(
                supply_item_id=supply_id,
                movement_type=MovementType.ENTRY,
                quantity=data.quantity,
                stock_before=stock_before,
                stock_after=new_total,
                notes=(
                    f"Lote {data.batch_code}"
                    + (f" — {data.vendor_name}" if data.vendor_name else "")
                ),
                unit_cost=data.unit_cost,
                alert_triggered=False,
                performed_by=performed_by_id,
            )

        await self._invalidate_supplies_cache()
        logger.info(
            "BATCH_CREATED supply=%s code=%s qty=%s cost=%s total=%s",
            supply_id, data.batch_code, data.quantity, data.unit_cost, new_total,
        )
        return BatchCreateResult(
            batch_id=batch.id,
            supply_id=supply_id,
            new_total_stock=new_total,
            total_movement_cost=total_cost,
        )

    async def list_batches(self, supply_id: uuid.UUID) -> BatchListResponse:
        batches = await self._batches.list_active_by_supply(supply_id)
        items = [BatchResponse.model_validate(b) for b in batches]
        total_stock = sum((b.current_stock for b in items), Decimal("0"))
        return BatchListResponse(items=items, total=len(items), total_stock=total_stock)

    async def consume_fifo(
        self,
        supply_id: uuid.UUID,
        quantity: Decimal,
        performed_by_id: uuid.UUID,
        user_role: UserRole,
        movement_type: MovementType = MovementType.EXIT,
        notes: str | None = None,
    ) -> FifoConsumptionResponse:
        """HU-13-02: consume `quantity` aplicando FIFO por vencimiento.

        Registra un único movimiento con el desglose por lote en las notas y
        dispara alerta si el stock total cae bajo el mínimo.
        """
        allowed = ALLOWED_MOVEMENTS_BY_ROLE.get(user_role, set())
        if movement_type not in allowed:
            raise MovementTypeNotAllowedError(
                movement_type=movement_type.value,
                allowed=[m.value for m in allowed],
            )

        lock_key = stock_lock_key(str(supply_id))
        async with acquire_lock(self._redis, lock_key, timeout_seconds=5):
            item = await self._supply_repo.get_by_id_for_update(supply_id)
            if item is None:
                raise ItemNotFoundError(str(supply_id))

            breakdown, weighted_cost = await self._deduct_fifo(
                supply_id, quantity, item.name
            )

            stock_before = item.current_stock
            new_total = await self._batches.sum_active_stock(supply_id)
            await self._supply_repo.update_stock(supply_id, new_total)
            alert_needed = new_total < item.minimum_stock

            desglose = "; ".join(
                f"{b.batch_code}:-{b.consumed}" for b in breakdown
            )
            unit_cost = (weighted_cost / quantity) if quantity else Decimal("0")
            movement = await self._movements.create(
                supply_item_id=supply_id,
                movement_type=movement_type,
                quantity=quantity,
                stock_before=stock_before,
                stock_after=new_total,
                notes=(notes + " | " if notes else "") + f"FIFO [{desglose}]",
                unit_cost=unit_cost,
                alert_triggered=alert_needed,
                performed_by=performed_by_id,
            )
            item_name, minimum = item.name, item.minimum_stock

        await self._invalidate_supplies_cache()
        if alert_needed:
            await self._alert.publish_low_stock(
                supply_item_id=supply_id,
                supply_name=item_name,
                current_stock=new_total,
                minimum_stock=minimum,
            )

        return FifoConsumptionResponse(
            supply_id=supply_id,
            movement_id=movement.id,
            total_consumed=quantity,
            new_total_stock=new_total,
            alert_triggered=alert_needed,
            breakdown=breakdown,
        )

    async def _deduct_fifo(
        self, supply_id: uuid.UUID, quantity: Decimal, item_name: str
    ) -> tuple[list[ConsumptionBreakdownItem], Decimal]:
        """Descuenta `quantity` de los lotes FIFO (bloqueados). Devuelve (desglose, costo).

        No hace commit; el caller controla la transacción (reutilizable por HU-15).
        Lanza InsufficientStockError si la suma de lotes no cubre la cantidad.
        """
        batches = await self._batches.list_active_fifo_for_update(supply_id)
        available = sum((b.current_stock for b in batches), Decimal("0"))
        if available < quantity:
            raise InsufficientStockError(
                available=available, requested=quantity, item_name=item_name
            )

        remaining = quantity
        breakdown: list[ConsumptionBreakdownItem] = []
        weighted_cost = Decimal("0")
        for batch in batches:
            if remaining <= 0:
                break
            take = min(batch.current_stock, remaining)
            new_stock = batch.current_stock - take
            await self._batches.apply_consumption(batch.id, new_stock)
            weighted_cost += take * batch.unit_cost
            remaining -= take
            breakdown.append(ConsumptionBreakdownItem(
                batch_id=batch.id,
                batch_code=batch.batch_code,
                consumed=take,
                remaining=new_stock,
            ))
        return breakdown, weighted_cost

    async def get_financials(self, start_date: date | None) -> FinancialsResponse:
        """HU-16-02: valor total de activos y pérdida acumulada por mermas."""
        batches = await self._batches.financial_active_batches()
        total_value = sum(
            (b.current_stock * b.unit_cost for b in batches), Decimal("0")
        )
        waste_loss = await self._movements.sum_waste_cost(start_date)
        return FinancialsResponse(
            total_active_value=total_value,
            total_waste_loss=waste_loss,
            active_batches_count=len(batches),
            period_start=start_date,
        )

    async def scan_expiring_batches(self, alert_days: int) -> int:
        """HU-13-03: publica alertas de lotes próximos a vencer y marca alert_sent.

        Pensado para ejecutarse como tarea programada (cada 24h). `alert_days`
        lo decide la pastelería desde Ajustes; quien invoca lo lee y lo pasa.
        Devuelve cuántas alertas se emitieron.
        """
        threshold = date.today() + timedelta(days=alert_days)
        batches = await self._batches.list_expiring(threshold)
        count = 0
        for batch in batches:
            days_left = (batch.expiration_date - date.today()).days
            await cache_publish(self._redis, ALERT_EXPIRATION_CHANNEL, {
                "batch_id": str(batch.id),
                "supply_item_id": str(batch.supply_item_id),
                "batch_code": batch.batch_code,
                "expiration_date": str(batch.expiration_date),
                "days_left": days_left,
                "alert_level": "EXPIRATION_CRITICAL",
            })
            await self._batches.mark_alert_sent(batch.id)
            count += 1
        if count:
            logger.info("EXPIRATION_ALERTS_PUBLISHED count=%s", count)
        return count

    async def _invalidate_supplies_cache(self) -> None:
        try:
            keys = [k async for k in self._redis.scan_iter(match=SUPPLIES_PAGE_PATTERN)]
            if keys:
                await self._redis.delete(*keys)
        except Exception as exc:  # noqa: BLE001
            logger.warning("REDIS_UNAVAILABLE invalidate_supplies err=%s", exc)
