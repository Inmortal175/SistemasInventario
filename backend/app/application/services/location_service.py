import logging
import uuid

from app.application.schemas.location_schema import (
    LocationCreate,
    LocationListResponse,
    LocationResponse,
)
from app.domain.exceptions import LocationCodeDuplicateError, LocationNotFoundError
from app.infrastructure.repositories.interfaces.i_location_repo import ILocationRepository

logger = logging.getLogger(__name__)


class LocationService:
    def __init__(self, repo: ILocationRepository) -> None:
        self._repo = repo

    async def create(
        self, data: LocationCreate, created_by_id: uuid.UUID | None = None
    ) -> LocationResponse:
        # El code ya llega normalizado y validado por el schema (LocationCode.parse).
        existing = await self._repo.get_by_code(data.code)
        if existing:
            raise LocationCodeDuplicateError(data.code)

        location = await self._repo.create(
            code=data.code,
            description=data.description,
            location_type=data.location_type,
            capacity_units=data.capacity_units,
            created_by=created_by_id,
        )
        logger.info("LOCATION_CREATED id=%s code=%s", location.id, location.code)
        return LocationResponse.model_validate(location)

    async def list_active(self) -> LocationListResponse:
        locations = await self._repo.list_active()
        items = [LocationResponse.model_validate(loc) for loc in locations]
        return LocationListResponse(items=items, total=len(items))

    async def deactivate(self, location_id: uuid.UUID) -> LocationResponse:
        location = await self._repo.deactivate(location_id)
        if location is None:
            raise LocationNotFoundError(str(location_id))
        return LocationResponse.model_validate(location)
