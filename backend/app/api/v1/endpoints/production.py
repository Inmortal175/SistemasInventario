from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.providers import ProductionServiceDep
import uuid

from app.application.schemas.recipe_schema import (
    ProductionHistoryResponse,
    ProductionPreparationResponse,
    ProductionRequest,
    ProductionResponse,
    ProductionSimulationResponse,
    RecipeCreate,
    RecipeListResponse,
    RecipeResponse,
)
from app.core.dependencies import CurrentUser, require_roles
from app.domain.enums import UserRole
from app.infrastructure.database.models.user_model import UserModel

router = APIRouter(tags=["Producción"])

_AdminOnly = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.SUPERADMIN))]


@router.post("/recipes", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    payload: RecipeCreate,
    service: ProductionServiceDep,
    current_user: _AdminOnly,
) -> RecipeResponse:
    """Crea una receta (BOM). Solo ADMIN+."""
    return await service.create_recipe(payload, created_by_id=current_user.id)


@router.get("/recipes", response_model=RecipeListResponse)
async def list_recipes(
    service: ProductionServiceDep,
    current_user: CurrentUser,
) -> RecipeListResponse:
    """Lista las recetas activas con sus ingredientes."""
    return await service.list_recipes()


@router.get("/production/history", response_model=ProductionHistoryResponse)
async def production_history(
    service: ProductionServiceDep,
    current_user: _AdminOnly,
    page: int = 1,
    limit: int = 20,
) -> ProductionHistoryResponse:
    """HU-17-02: historial de corridas de producción (qué, cuánto, quién, cuándo). ADMIN+."""
    return await service.list_production_history(page=page, limit=limit)


@router.get(
    "/production/{production_id}/preparation",
    response_model=ProductionPreparationResponse,
)
async def production_preparation(
    production_id: uuid.UUID,
    service: ProductionServiceDep,
    current_user: _AdminOnly,
) -> ProductionPreparationResponse:
    """HU-17: lista de preparación de una corrida ya producida (cómo se fabricó). ADMIN+.

    Snapshot inmutable: qué insumo, cuánto, en qué unidad, de qué ubicación y de
    qué lotes salió. 404 si la corrida no existe.
    """
    return await service.get_preparation(production_id)


@router.post("/production/simulate", response_model=ProductionSimulationResponse)
async def simulate_production(
    payload: ProductionRequest,
    service: ProductionServiceDep,
    current_user: CurrentUser,
) -> ProductionSimulationResponse:
    """HU-15: Simulacro de stock (dry-run). Verifica si hay insumos suficientes
    para producir N unidades SIN descontar nada. Devuelve el desglose por
    ingrediente y los faltantes con su déficit. STAFF+ puede simular.
    """
    return await service.simulate(
        recipe_id=payload.recipe_id, quantity=payload.quantity
    )


@router.post(
    "/production/produce",
    response_model=ProductionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def produce(
    payload: ProductionRequest,
    service: ProductionServiceDep,
    current_user: CurrentUser,
) -> ProductionResponse:
    """HU-15: Registra la producción de un lote de producto final.

    STAFF+ puede producir. Descuenta ingredientes por FIFO de forma atómica;
    si falta stock de algún ingrediente, hace ROLLBACK total (422).
    """
    return await service.produce(
        recipe_id=payload.recipe_id,
        quantity=payload.quantity,
        performed_by_id=current_user.id,
    )
