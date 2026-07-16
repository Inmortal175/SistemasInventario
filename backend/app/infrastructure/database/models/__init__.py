# Importar todos los modelos aquí para que Alembic los detecte en autogenerate
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.models.category_model import CategoryModel
from app.infrastructure.database.models.location_model import LocationModel
from app.infrastructure.database.models.supply_model import SupplyItemModel
from app.infrastructure.database.models.movement_model import MovementHistoryModel
from app.infrastructure.database.models.batch_model import SupplyBatchModel
from app.infrastructure.database.models.recipe_model import RecipeModel, RecipeItemModel
from app.infrastructure.database.models.production_model import (
    ProductionRunItemModel,
    ProductionRunModel,
)
from app.infrastructure.database.models.settings_model import SystemSettingsModel

__all__ = [
    "SystemSettingsModel",
    "UserModel",
    "CategoryModel",
    "LocationModel",
    "SupplyItemModel",
    "MovementHistoryModel",
    "SupplyBatchModel",
    "RecipeModel",
    "RecipeItemModel",
    "ProductionRunModel",
    "ProductionRunItemModel",
]
