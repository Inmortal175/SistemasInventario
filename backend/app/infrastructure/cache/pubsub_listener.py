import asyncio
import json
import logging

from redis.exceptions import RedisError

from app.api.v1.endpoints.websocket import ADMIN_GROUP, manager
from app.infrastructure.cache.cache_keys import (
    ALERT_EXPIRATION_CHANNEL,
    ALERT_LOW_STOCK_CHANNEL,
)
from app.infrastructure.cache.redis_client import get_redis

logger = logging.getLogger(__name__)


async def redis_alert_listener() -> None:
    """HU-14-02: escucha los canales de alertas en Redis y los retransmite por WS.

    Diseñado para correr como tarea en background durante toda la vida de la app.
    Reintenta ante caídas de Redis sin tumbar el proceso.
    """
    channels = [ALERT_LOW_STOCK_CHANNEL, ALERT_EXPIRATION_CHANNEL]
    while True:
        try:
            redis = await get_redis()
            pubsub = redis.pubsub()
            await pubsub.subscribe(*channels)
            logger.info("PUBSUB_LISTENER subscribed channels=%s", channels)

            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                channel = message["channel"]
                try:
                    data = json.loads(message["data"])
                except (json.JSONDecodeError, TypeError):
                    data = {"raw": message["data"]}

                event_type = (
                    "low_stock"
                    if channel == ALERT_LOW_STOCK_CHANNEL
                    else "expiration_critical"
                )
                await manager.broadcast(ADMIN_GROUP, {
                    "type": event_type,
                    "channel": channel,
                    "data": data,
                })
        except asyncio.CancelledError:
            logger.info("PUBSUB_LISTENER cancelled")
            raise
        except RedisError as exc:
            logger.warning("PUBSUB_LISTENER redis err=%s — reintentando en 5s", exc)
            await asyncio.sleep(5)
        except Exception as exc:  # noqa: BLE001
            logger.error("PUBSUB_LISTENER error inesperado=%s — reintentando en 5s", exc)
            await asyncio.sleep(5)
