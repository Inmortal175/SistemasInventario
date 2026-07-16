import logging
from datetime import datetime, timedelta, timezone

from redis.asyncio import Redis

from app.application.schemas.dashboard_schema import KpisResponse, TopWastedSupply
from app.infrastructure.cache.cache_keys import DASHBOARD_KPIS_KEY
from app.infrastructure.cache.redis_client import cache_get, cache_set
from app.infrastructure.repositories.movement_repository import MovementRepository
from app.infrastructure.repositories.supply_repository import SupplyRepository

logger = logging.getLogger(__name__)

# TTL corto: los KPIs son "tiempo real" pero toleran unos segundos de staleness.
_KPIS_TTL = 30


class DashboardService:
    """HU-08: KPIs consolidados con lectura cache-first desde Redis."""

    def __init__(
        self,
        supply_repo: SupplyRepository,
        movement_repo: MovementRepository,
        redis: Redis,
    ) -> None:
        self._supplies = supply_repo
        self._movements = movement_repo
        self._redis = redis

    async def get_kpis(self) -> KpisResponse:
        cached = await cache_get(self._redis, DASHBOARD_KPIS_KEY)
        if cached is not None:
            return KpisResponse(**{**cached, "source": "cache"})

        critical = await self._supplies.list_below_minimum()
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        movements_24h = await self._movements.count_since(since)

        top_rows = await self._movements.top_wasted_supplies(limit=5)
        top_wasted: list[TopWastedSupply] = []
        for supply_id, total in top_rows:
            item = await self._supplies.get_by_id(supply_id)
            top_wasted.append(TopWastedSupply(
                supply_id=str(supply_id),
                supply_name=item.name if item else "(desconocido)",
                total_wasted=str(total),
            ))

        response = KpisResponse(
            total_critical_items=len(critical),
            movements_last_24h=movements_24h,
            top_wasted_supplies=top_wasted,
            source="database",
        )
        await cache_set(self._redis, DASHBOARD_KPIS_KEY, response.model_dump(), ttl=_KPIS_TTL)
        return response
