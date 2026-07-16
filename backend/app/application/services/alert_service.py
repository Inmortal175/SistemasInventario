import logging
import uuid
from decimal import Decimal

from redis.asyncio import Redis

from app.infrastructure.cache.cache_keys import ALERT_LOW_STOCK_CHANNEL
from app.infrastructure.cache.redis_client import cache_publish

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def publish_low_stock(
        self,
        supply_item_id: uuid.UUID,
        supply_name: str,
        current_stock: Decimal,
        minimum_stock: Decimal,
    ) -> None:
        deficit = minimum_stock - current_stock
        payload = {
            "supply_item_id": str(supply_item_id),
            "supply_name": supply_name,
            "current_stock": str(current_stock),
            "minimum_stock": str(minimum_stock),
            "deficit": str(deficit),
            "alert_level": "WARNING",
        }
        published = await cache_publish(self._redis, ALERT_LOW_STOCK_CHANNEL, payload)
        if published:
            logger.info(
                "ALERT_LOW_STOCK item=%s current=%s minimum=%s deficit=%s",
                supply_name, current_stock, minimum_stock, deficit,
            )
        else:
            logger.error(
                "ALERT_PUBLISH_FAILED item=%s — Redis no disponible",
                supply_name,
            )
