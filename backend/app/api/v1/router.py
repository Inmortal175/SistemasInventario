from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    batches,
    categories,
    dashboard,
    locations,
    movements,
    production,
    reports,
    settings,
    supplies,
    users,
    websocket,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(locations.router)
api_router.include_router(supplies.router)
api_router.include_router(batches.router)
api_router.include_router(movements.router)
api_router.include_router(users.router)
api_router.include_router(production.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)
api_router.include_router(settings.router)
api_router.include_router(websocket.router)
