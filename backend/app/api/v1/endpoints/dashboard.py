from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.providers import BatchServiceDep, DashboardServiceDep
from app.application.schemas.batch_schema import FinancialsResponse
from app.application.schemas.dashboard_schema import KpisResponse
from app.core.dependencies import require_roles
from app.domain.enums import UserRole
from app.infrastructure.database.models.user_model import UserModel

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_AdminOnly = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.SUPERADMIN))]


@router.get("/kpis", response_model=KpisResponse)
async def get_kpis(
    service: DashboardServiceDep,
    current_user: _AdminOnly,
) -> KpisResponse:
    """HU-08-01: KPIs consolidados en tiempo real (cache-first en Redis). ADMIN+."""
    return await service.get_kpis()


@router.get("/financials", response_model=FinancialsResponse)
async def get_financials(
    service: BatchServiceDep,
    current_user: _AdminOnly,
    start_date: Annotated[date | None, Query()] = None,
) -> FinancialsResponse:
    """HU-16-02: Valor financiero activo del almacén y pérdida por mermas. ADMIN+."""
    return await service.get_financials(start_date)
