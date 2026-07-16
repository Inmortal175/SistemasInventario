from fastapi import APIRouter, Response, status

from app.api.v1.providers import SupplyServiceDep
from app.application.schemas.movement_schema import MovementCreate, MovementResponse
from app.core.dependencies import CurrentUser

router = APIRouter(prefix="/movements", tags=["Movimientos"])


@router.post("", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
async def register_movement(
    payload: MovementCreate,
    service: SupplyServiceDep,
    current_user: CurrentUser,
    response: Response,
) -> MovementResponse:
    """HU-02: Registra un movimiento de inventario.

    El servicio valida RBAC (STAFF solo EXIT/WASTE), stock disponible,
    aplica lock distribuido y dispara alerta si el stock cae bajo el mínimo.
    """
    result = await service.register_movement(
        data=payload,
        performed_by_id=current_user.id,
        user_role=current_user.role,
    )
    if result.alert_triggered:
        response.headers["X-Alert-Triggered"] = "true"
    return result
