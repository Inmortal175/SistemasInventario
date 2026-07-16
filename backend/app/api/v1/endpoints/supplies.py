import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.v1.providers import SupplyServiceDep
from app.application.schemas.movement_schema import (
    MovementHistoryListResponse,
    ReconciliationRequest,
    ReconciliationResponse,
)
from app.application.schemas.supply_schema import (
    SupplyItemCreate,
    SupplyItemListResponse,
    SupplyItemResponse,
)
from app.core.dependencies import CurrentUser, require_roles
from app.domain.enums import ItemType, UserRole
from app.infrastructure.database.models.user_model import UserModel

router = APIRouter(prefix="/supplies", tags=["Insumos"])

_AdminOnly = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.SUPERADMIN))]


@router.post("", response_model=SupplyItemResponse, status_code=status.HTTP_201_CREATED)
async def create_supply(
    payload: SupplyItemCreate,
    service: SupplyServiceDep,
    current_user: _AdminOnly,
) -> SupplyItemResponse:
    """Alta de un insumo. Solo ADMIN+."""
    return await service.create(data=payload, created_by_id=current_user.id)


@router.get("", response_model=SupplyItemListResponse)
async def list_supplies(
    service: SupplyServiceDep,
    current_user: CurrentUser,
    response: Response,
    category_id: Annotated[uuid.UUID | None, Query()] = None,
    location_id: Annotated[uuid.UUID | None, Query()] = None,
    item_type: Annotated[ItemType | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SupplyItemListResponse:
    """HU-06: Lista insumos activos paginados (cache-first) con filtros.

    ``item_type`` separa insumos (INGREDIENT) de productos terminados
    (FINISHED_PRODUCT). Devuelve el header ``X-Cache: HIT|MISS``.
    """
    result, cache_status = await service.list_active(
        category_id=category_id, location_id=location_id,
        item_type=item_type, page=page, limit=limit,
    )
    response.headers["X-Cache"] = cache_status
    return result


@router.get("/{supply_id}", response_model=SupplyItemResponse)
async def get_supply(
    supply_id: uuid.UUID,
    service: SupplyServiceDep,
    current_user: CurrentUser,
) -> SupplyItemResponse:
    """HU-06: detalle de un insumo por id. 404 si no existe."""
    return await service.get_detail(supply_id)


@router.post("/reconciliation", response_model=ReconciliationResponse)
async def reconcile_stock(
    payload: ReconciliationRequest,
    service: SupplyServiceDep,
    current_user: _AdminOnly,
    response: Response,
) -> ReconciliationResponse:
    """HU-11: Conciliación de inventario por conteo físico. Solo ADMIN+.

    STAFF recibe 403 (dependencia _AdminOnly). Registra un ADJUSTMENT trazable
    sin alterar la inmutabilidad del historial.
    """
    result = await service.reconcile(
        supply_id=payload.supply_id,
        physical_stock=payload.physical_stock,
        reason=payload.reason,
        performed_by_id=current_user.id,
    )
    if result.alert_triggered:
        response.headers["X-Alert-Triggered"] = "true"
    return result


@router.get("/{supply_id}/movements", response_model=MovementHistoryListResponse)
async def list_supply_movements(
    supply_id: uuid.UUID,
    service: SupplyServiceDep,
    current_user: _AdminOnly,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> MovementHistoryListResponse:
    """HU-07: Historial de movimientos de un insumo (auditoría). Solo ADMIN+.

    Ordenado descendentemente por fecha, paginado, con el email del usuario
    que ejecutó cada movimiento.
    """
    return await service.list_movements(supply_id=supply_id, page=page, limit=limit)
