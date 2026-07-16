"""Proveedores de dependencias (DI): ensamblan servicios con sus repositorios.

Cada provider recibe la sesión de BD y el cliente Redis vía Depends(),
construye los repositorios concretos y los inyecta en el servicio.
Esto mantiene los endpoints libres de lógica de wiring (SRP).
"""
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.alert_service import AlertService
from app.application.services.auth_service import AuthService
from app.application.services.category_service import CategoryService
from app.application.services.location_service import LocationService
from app.application.services.batch_service import BatchService
from app.application.services.dashboard_service import DashboardService
from app.application.services.production_service import ProductionService
from app.application.services.report_service import ReportService
from app.application.services.settings_service import SettingsService
from app.application.services.supply_service import SupplyService
from app.application.services.user_service import UserService
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.database.connection import get_async_session
from app.infrastructure.repositories.batch_repository import BatchRepository
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.infrastructure.repositories.location_repository import LocationRepository
from app.infrastructure.repositories.movement_repository import MovementRepository
from app.infrastructure.repositories.production_run_repository import (
    ProductionRunRepository,
)
from app.infrastructure.repositories.recipe_repository import RecipeRepository
from app.infrastructure.repositories.settings_repository import SettingsRepository
from app.infrastructure.repositories.supply_repository import SupplyRepository
from app.infrastructure.repositories.user_repository import UserRepository


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> AuthService:
    return AuthService(user_repo=UserRepository(session), redis=redis)


def get_category_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> CategoryService:
    return CategoryService(repo=CategoryRepository(session), redis=redis)


def get_location_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> LocationService:
    return LocationService(repo=LocationRepository(session))


def get_supply_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> SupplyService:
    return SupplyService(
        supply_repo=SupplyRepository(session),
        movement_repo=MovementRepository(session),
        alert_service=AlertService(redis=redis),
        redis=redis,
    )


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> UserService:
    return UserService(
        user_repo=UserRepository(session),
        category_repo=CategoryRepository(session),
        location_repo=LocationRepository(session),
        movement_repo=MovementRepository(session),
        redis=redis,
    )


def get_batch_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> BatchService:
    return BatchService(
        supply_repo=SupplyRepository(session),
        batch_repo=BatchRepository(session),
        movement_repo=MovementRepository(session),
        alert_service=AlertService(redis=redis),
        redis=redis,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
LocationServiceDep = Annotated[LocationService, Depends(get_location_service)]
SupplyServiceDep = Annotated[SupplyService, Depends(get_supply_service)]
def get_dashboard_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> DashboardService:
    return DashboardService(
        supply_repo=SupplyRepository(session),
        movement_repo=MovementRepository(session),
        redis=redis,
    )


def get_production_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> ProductionService:
    return ProductionService(
        recipe_repo=RecipeRepository(session),
        supply_repo=SupplyRepository(session),
        batch_repo=BatchRepository(session),
        movement_repo=MovementRepository(session),
        production_run_repo=ProductionRunRepository(session),
        category_repo=CategoryRepository(session),
        location_repo=LocationRepository(session),
        alert_service=AlertService(redis=redis),
        redis=redis,
    )


def get_report_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ReportService:
    return ReportService(movement_repo=MovementRepository(session))


def get_settings_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> SettingsService:
    return SettingsService(repo=SettingsRepository(session), redis=redis)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
BatchServiceDep = Annotated[BatchService, Depends(get_batch_service)]
DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
ProductionServiceDep = Annotated[ProductionService, Depends(get_production_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
SettingsServiceDep = Annotated[SettingsService, Depends(get_settings_service)]
