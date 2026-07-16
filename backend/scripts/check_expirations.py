"""Alerta predictiva de lotes próximos a vencer (HU-13-03).

Recorre `supply_batches` buscando lotes activos que vencen dentro del umbral
configurado en Ajustes (`expiration_alert_days`, 5 días por defecto), publica una
alerta en el canal Redis "alerts:expiration_critical" y marca `alert_sent=true`
para no repetir la alerta.

Pensado para ejecutarse como tarea programada cada 24 horas:
    docker-compose exec backend python scripts/check_expirations.py

O vía cron del host / un scheduler (APScheduler, Celery beat, etc.).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.services.alert_service import AlertService  # noqa: E402
from app.application.services.batch_service import BatchService  # noqa: E402
from app.infrastructure.cache.redis_client import close_redis, get_redis  # noqa: E402
from app.infrastructure.database.connection import AsyncSessionLocal, engine  # noqa: E402
from app.infrastructure.repositories.batch_repository import BatchRepository  # noqa: E402
from app.infrastructure.repositories.movement_repository import MovementRepository  # noqa: E402
from app.infrastructure.repositories.settings_repository import SettingsRepository  # noqa: E402
from app.infrastructure.repositories.supply_repository import SupplyRepository  # noqa: E402


async def main() -> int:
    redis = await get_redis()
    try:
        async with AsyncSessionLocal() as session:
            config = await SettingsRepository(session).get()
            alert_days = config.expiration_alert_days

            service = BatchService(
                supply_repo=SupplyRepository(session),
                batch_repo=BatchRepository(session),
                movement_repo=MovementRepository(session),
                alert_service=AlertService(redis=redis),
                redis=redis,
            )
            count = await service.scan_expiring_batches(alert_days)
            await session.commit()
        print(f"✅ Alertas de vencimiento publicadas: {count} (umbral: {alert_days} días)")
        return 0
    finally:
        await close_redis()
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
