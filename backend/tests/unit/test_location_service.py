"""
TC-LOC-SVC-01 a TC-LOC-SVC-04
Pruebas unitarias del LocationService — sin BD real (repositorio mockeado).
"""
import uuid
from unittest.mock import MagicMock

import pytest

from app.application.schemas.location_schema import LocationCreate
from app.application.services.location_service import LocationService
from app.domain.enums import LocationType
from app.domain.exceptions import LocationCodeDuplicateError, LocationNotFoundError
from app.infrastructure.database.models.location_model import LocationModel


def _make_location_model(code: str = "EST-05") -> MagicMock:
    loc = MagicMock(spec=LocationModel)
    loc.id = uuid.uuid4()
    loc.code = code
    loc.description = None
    loc.location_type = LocationType.SHELF
    loc.capacity_units = 20
    loc.is_active = True
    return loc


# ── TC-LOC-SVC-01 — Código duplicado rechazado sin insertar ──────────────────

@pytest.mark.asyncio
async def test_TC_LOC_SVC_01_duplicate_code_raises(mock_location_repo):
    mock_location_repo.get_by_code.return_value = _make_location_model("REF-02")
    service = LocationService(repo=mock_location_repo)

    data = LocationCreate(code="REF-02", location_type=LocationType.REFRIGERATOR)

    with pytest.raises(LocationCodeDuplicateError) as exc_info:
        await service.create(data=data)

    assert exc_info.value.error_code == "LOCATION_CODE_ALREADY_EXISTS"
    mock_location_repo.create.assert_not_called()


# ── TC-LOC-SVC-02 — Creación exitosa persiste y devuelve la respuesta ────────

@pytest.mark.asyncio
async def test_TC_LOC_SVC_02_successful_creation(mock_location_repo):
    mock_location_repo.get_by_code.return_value = None
    mock_location_repo.create.return_value = _make_location_model("EST-05")
    service = LocationService(repo=mock_location_repo)

    data = LocationCreate(code="EST-05", location_type=LocationType.SHELF, capacity_units=20)
    result = await service.create(data=data)

    assert result.code == "EST-05"
    assert result.is_active is True
    mock_location_repo.create.assert_called_once()


# ── TC-LOC-SVC-03 — Listado activo mapea a la respuesta paginada ─────────────

@pytest.mark.asyncio
async def test_TC_LOC_SVC_03_list_active(mock_location_repo):
    mock_location_repo.list_active.return_value = [
        _make_location_model("EST-01"),
        _make_location_model("REF-02"),
    ]
    service = LocationService(repo=mock_location_repo)

    result = await service.list_active()

    assert result.total == 2
    assert {item.code for item in result.items} == {"EST-01", "REF-02"}


# ── TC-LOC-SVC-04 — Desactivar ubicación inexistente lanza 404 ───────────────

@pytest.mark.asyncio
async def test_TC_LOC_SVC_04_deactivate_missing_raises(mock_location_repo):
    mock_location_repo.deactivate.return_value = None
    service = LocationService(repo=mock_location_repo)

    with pytest.raises(LocationNotFoundError) as exc_info:
        await service.deactivate(uuid.uuid4())

    assert exc_info.value.error_code == "LOCATION_NOT_FOUND"
