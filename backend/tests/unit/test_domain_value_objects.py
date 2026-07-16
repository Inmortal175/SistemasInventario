"""
TC-DOMAIN-01 a TC-DOMAIN-08
Pruebas unitarias puras de la capa de dominio.
Sin dependencias de red, DB ni Redis.
"""
import pytest

from app.domain.enums import LocationType, UserRole, MovementType, ALLOWED_MOVEMENTS_BY_ROLE
from app.domain.exceptions import (
    LocationCodeInvalidError,
    InsufficientStockError,
    MovementTypeNotAllowedError,
)
from app.domain.value_objects import LocationCode
from decimal import Decimal


# ── LocationCode — códigos válidos ────────────────────────────────────────────

@pytest.mark.parametrize("code,expected_type,expected_row", [
    ("EST-01",    LocationType.SHELF,        None),
    ("EST-01-F2", LocationType.SHELF,        2),
    ("EST-12-F1", LocationType.SHELF,        1),
    ("REF-02",    LocationType.REFRIGERATOR, None),
    ("FRZ-01",    LocationType.FREEZER,      None),
    ("CAB-03",    LocationType.CABINET,      None),
    ("CON-01",    LocationType.COUNTER,      None),
    ("ALM-99",    LocationType.WAREHOUSE,    None),
])
def test_location_code_valid(code: str, expected_type: LocationType, expected_row: int | None) -> None:
    loc = LocationCode.parse(code)
    assert loc.value == code
    assert loc.location_type == expected_type
    assert loc.row == expected_row


# ── LocationCode — normalización a mayúsculas ─────────────────────────────────

def test_location_code_parse_normalizes_to_uppercase() -> None:
    loc = LocationCode.parse("est-01-f2")
    assert loc.value == "EST-01-F2"
    assert loc.location_type == LocationType.SHELF


# ── LocationCode — códigos inválidos ─────────────────────────────────────────

@pytest.mark.parametrize("bad_code", [
    "EST-1",        # número de un solo dígito
    "EST-001",      # tres dígitos
    "REF-01-F2",    # REF no admite fila
    "FRZ-02-F1",    # FRZ no admite fila
    "CAB-01-F3",    # CAB no admite fila
    "XYZ-01",       # prefijo desconocido
    "EST01",        # sin guión
    "",             # vacío
    "EST-00-F0",    # fila 0 (fuera de rango semántico — el patrón permite \d{1,2})
    "EST-01-f2",    # minúscula en fila (normalizar con .parse() primero)
])
def test_location_code_invalid_raises(bad_code: str) -> None:
    with pytest.raises(LocationCodeInvalidError) as exc_info:
        LocationCode(value=bad_code)
    assert exc_info.value.error_code == "LOCATION_CODE_INVALID"


# ── InsufficientStockError — atributos de contexto ───────────────────────────

def test_insufficient_stock_error_carries_context() -> None:
    err = InsufficientStockError(
        available=Decimal("3.000"),
        requested=Decimal("5.000"),
        item_name="Harina de Trigo 000",
    )
    assert err.available == Decimal("3.000")
    assert err.requested == Decimal("5.000")
    assert err.error_code == "INSUFFICIENT_STOCK"
    assert "Harina de Trigo 000" in err.message


# ── RBAC — movimientos permitidos por rol ────────────────────────────────────

def test_staff_can_only_exit_and_waste() -> None:
    allowed = ALLOWED_MOVEMENTS_BY_ROLE[UserRole.STAFF]
    assert MovementType.EXIT in allowed
    assert MovementType.WASTE in allowed
    assert MovementType.ENTRY not in allowed
    assert MovementType.ADJUSTMENT_ADD not in allowed
    assert MovementType.ADJUSTMENT_SUB not in allowed
    assert MovementType.TRANSFER not in allowed


def test_admin_can_use_all_movement_types() -> None:
    allowed = ALLOWED_MOVEMENTS_BY_ROLE[UserRole.ADMIN]
    assert allowed == set(MovementType)


def test_superadmin_can_use_all_movement_types() -> None:
    allowed = ALLOWED_MOVEMENTS_BY_ROLE[UserRole.SUPERADMIN]
    assert allowed == set(MovementType)
