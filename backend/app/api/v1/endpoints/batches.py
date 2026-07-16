import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.v1.providers import BatchServiceDep
from app.application.schemas.batch_schema import (
    BatchCreate,
    BatchCreateResult,
    BatchListResponse,
    FifoConsumptionResponse,
)
from app.application.schemas.movement_schema import MovementCreate
from app.core.dependencies import CurrentUser, require_roles
from app.domain.enums import UserRole
from app.infrastructure.database.models.user_model import UserModel

router = APIRouter(prefix="/supplies", tags=["Lotes"])

_AdminOnly = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.SUPERADMIN))]


@router.post(
    "/{supply_id}/batches",
    response_model=BatchCreateResult,
    status_code=status.HTTP_201_CREATED,
)
async def create_batch(
    supply_id: uuid.UUID,
    payload: BatchCreate,
    service: BatchServiceDep,
    current_user: _AdminOnly,
) -> BatchCreateResult:
    """HU-13-01 / HU-16-01: Alta de lote perecedero (ENTRY) con costo y proveedor. ADMIN+."""
    return await service.create_batch(
        supply_id=supply_id, data=payload, performed_by_id=current_user.id
    )


@router.get("/{supply_id}/batches", response_model=BatchListResponse)
async def list_batches(
    supply_id: uuid.UUID,
    service: BatchServiceDep,
    current_user: CurrentUser,
) -> BatchListResponse:
    """Lista los lotes activos de un insumo, ordenados por vencimiento (FIFO)."""
    return await service.list_batches(supply_id)


@router.post(
    "/{supply_id}/batches/consume",
    response_model=FifoConsumptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def consume_fifo(
    supply_id: uuid.UUID,
    payload: MovementCreate,
    service: BatchServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> FifoConsumptionResponse:
    """HU-13-02: Consumo (EXIT/WASTE) aplicando FIFO por vencimiento.

    El servicio valida RBAC (STAFF solo EXIT/WASTE) y devuelve el desglose por lote.
    """
    result = await service.consume_fifo(
        supply_id=supply_id,
        quantity=payload.quantity,
        performed_by_id=current_user.id,
        user_role=current_user.role,
        movement_type=payload.movement_type,
        notes=payload.notes,
    )
    if result.alert_triggered:
        response.headers["X-Alert-Triggered"] = "true"
    return result
