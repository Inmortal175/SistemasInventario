"""Pruebas de integración de la capa API (endpoints → servicios → repos → BD/Redis).

Cubren autenticación, categorías (HU-01), ubicaciones (HU-03), insumos y
movimientos (HU-02) contra PostgreSQL y Redis reales.
"""
from httpx import AsyncClient

API = "/api/v1"


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _create_category(client: AsyncClient, headers: dict, name: str = "Harinas") -> dict:
    resp = await client.post(
        f"{API}/categories",
        json={"name": name, "color_hex": "#FF6B9D", "icon_name": "wheat"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_location(client: AsyncClient, headers: dict, code: str = "EST-05") -> dict:
    resp = await client.post(
        f"{API}/locations",
        json={"code": code, "location_type": "SHELF", "capacity_units": 20},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_supply(
    client: AsyncClient,
    headers: dict,
    category_id: str,
    location_id: str,
    *,
    sku: str = "HAR-001",
    current: str = "25.000",
    minimum: str = "10.000",
) -> dict:
    resp = await client.post(
        f"{API}/supplies",
        json={
            "name": "Harina de Trigo 000",
            "sku": sku,
            "category_id": category_id,
            "location_id": location_id,
            "unit_of_measure": "KG",
            "current_stock": current,
            "minimum_stock": minimum,
            "maximum_stock": "100.000",
            "unit_cost": "3.5000",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Sistema ───────────────────────────────────────────────────────────────────

async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Autenticación (HU-04) ─────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient, admin_ctx) -> None:
    resp = await client.post(
        f"{API}/auth/login",
        data={"username": admin_ctx.email, "password": admin_ctx.password},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["role"] == "ADMIN"


async def test_login_wrong_password(client: AsyncClient, admin_ctx) -> None:
    # SC-HU04-02: credenciales inválidas → 401 Unauthorized.
    resp = await client.post(
        f"{API}/auth/login",
        data={"username": admin_ctx.email, "password": "wrong-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "INVALID_CREDENTIALS"


async def test_me_returns_profile(client: AsyncClient, admin_ctx) -> None:
    resp = await client.get(f"{API}/auth/me", headers=admin_ctx.headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == admin_ctx.email


async def test_me_without_token_unauthorized(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/auth/me")
    assert resp.status_code == 401


async def test_invalid_token_unauthorized(client: AsyncClient) -> None:
    resp = await client.get(
        f"{API}/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401
    # HTTPException anida el payload bajo "detail"
    assert resp.json()["detail"]["error_code"] == "INVALID_CREDENTIALS"


# ── Categorías (HU-01) ────────────────────────────────────────────────────────

async def test_create_category_admin(client: AsyncClient, admin_ctx) -> None:
    resp = await client.post(
        f"{API}/categories",
        json={"name": "Colorantes Artificiales", "color_hex": "#00AAFF"},
        headers=admin_ctx.headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["slug"] == "colorantes-artificiales"
    assert body["is_active"] is True
    assert resp.headers.get("X-Cache-Status") == "WRITE"


async def test_create_category_duplicate_conflict(client: AsyncClient, admin_ctx) -> None:
    await _create_category(client, admin_ctx.headers, name="Harinas Especiales")
    resp = await client.post(
        f"{API}/categories",
        json={"name": "Harinas Especiales", "color_hex": "#123456"},
        headers=admin_ctx.headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "CATEGORY_NAME_ALREADY_EXISTS"


async def test_create_category_staff_forbidden(client: AsyncClient, staff_ctx) -> None:
    resp = await client.post(
        f"{API}/categories",
        json={"name": "Prohibida", "color_hex": "#000000"},
        headers=staff_ctx.headers,
    )
    assert resp.status_code == 403
    # require_roles lanza HTTPException → payload anidado bajo "detail"
    assert resp.json()["detail"]["error_code"] == "INSUFFICIENT_PERMISSIONS"


async def test_list_and_deactivate_category(client: AsyncClient, admin_ctx) -> None:
    created = await _create_category(client, admin_ctx.headers, name="Coberturas")

    listed = await client.get(f"{API}/categories", headers=admin_ctx.headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    deleted = await client.delete(
        f"{API}/categories/{created['id']}", headers=admin_ctx.headers
    )
    assert deleted.status_code == 200
    assert deleted.json()["is_active"] is False


# ── Ubicaciones (HU-03) ───────────────────────────────────────────────────────

async def test_create_location_admin_normalizes_code(client: AsyncClient, admin_ctx) -> None:
    resp = await client.post(
        f"{API}/locations",
        json={"code": "est-07-f2", "location_type": "SHELF"},
        headers=admin_ctx.headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["code"] == "EST-07-F2"


async def test_create_location_invalid_code_unprocessable(client: AsyncClient, admin_ctx) -> None:
    # REF no admite sufijo de fila → el validador del schema lo rechaza (422)
    resp = await client.post(
        f"{API}/locations",
        json={"code": "REF-01-F2", "location_type": "REFRIGERATOR"},
        headers=admin_ctx.headers,
    )
    assert resp.status_code == 422


async def test_create_location_duplicate_conflict(client: AsyncClient, admin_ctx) -> None:
    await _create_location(client, admin_ctx.headers, code="REF-02")
    resp = await client.post(
        f"{API}/locations",
        json={"code": "REF-02", "location_type": "REFRIGERATOR"},
        headers=admin_ctx.headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "LOCATION_CODE_ALREADY_EXISTS"


async def test_create_location_staff_forbidden(client: AsyncClient, staff_ctx) -> None:
    resp = await client.post(
        f"{API}/locations",
        json={"code": "FRZ-01", "location_type": "FREEZER"},
        headers=staff_ctx.headers,
    )
    assert resp.status_code == 403


async def test_list_and_deactivate_location(client: AsyncClient, admin_ctx) -> None:
    created = await _create_location(client, admin_ctx.headers, code="ALM-09")

    listed = await client.get(f"{API}/locations", headers=admin_ctx.headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    deleted = await client.delete(
        f"{API}/locations/{created['id']}", headers=admin_ctx.headers
    )
    assert deleted.status_code == 200
    assert deleted.json()["is_active"] is False


async def test_deactivate_missing_location_not_found(client: AsyncClient, admin_ctx) -> None:
    ghost = "00000000-0000-0000-0000-000000000000"
    resp = await client.delete(f"{API}/locations/{ghost}", headers=admin_ctx.headers)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "LOCATION_NOT_FOUND"


# ── Insumos + Movimientos (HU-02) ─────────────────────────────────────────────

async def test_create_and_list_supply(client: AsyncClient, admin_ctx) -> None:
    cat = await _create_category(client, admin_ctx.headers)
    loc = await _create_location(client, admin_ctx.headers)
    supply = await _create_supply(client, admin_ctx.headers, cat["id"], loc["id"])
    assert supply["sku"] == "HAR-001"

    listed = await client.get(f"{API}/supplies", headers=admin_ctx.headers)
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    assert body["low_stock_count"] == 0


async def test_get_supply_detail_ok(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    cat = await _create_category(client, admin_ctx.headers)
    loc = await _create_location(client, admin_ctx.headers)
    supply = await _create_supply(client, admin_ctx.headers, cat["id"], loc["id"])

    # Cualquier usuario autenticado (incluido STAFF) puede ver el detalle.
    resp = await client.get(f"{API}/supplies/{supply['id']}", headers=staff_ctx.headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == supply["id"]
    assert body["sku"] == "HAR-001"
    assert body["is_below_minimum"] is False


async def test_get_supply_detail_missing_not_found(client: AsyncClient, admin_ctx) -> None:
    ghost = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"{API}/supplies/{ghost}", headers=admin_ctx.headers)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "SUPPLY_ITEM_NOT_FOUND_OR_INACTIVE"


async def test_staff_exit_movement_no_alert(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    cat = await _create_category(client, admin_ctx.headers)
    loc = await _create_location(client, admin_ctx.headers)
    supply = await _create_supply(
        client, admin_ctx.headers, cat["id"], loc["id"], current="25.000", minimum="10.000"
    )

    resp = await client.post(
        f"{API}/movements",
        json={"supply_item_id": supply["id"], "movement_type": "EXIT", "quantity": "5.000"},
        headers=staff_ctx.headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["stock_after"] == "20.000"
    assert body["alert_triggered"] is False


async def test_staff_exit_movement_triggers_alert(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    cat = await _create_category(client, admin_ctx.headers)
    loc = await _create_location(client, admin_ctx.headers)
    supply = await _create_supply(
        client, admin_ctx.headers, cat["id"], loc["id"], current="12.000", minimum="10.000"
    )

    resp = await client.post(
        f"{API}/movements",
        json={"supply_item_id": supply["id"], "movement_type": "EXIT", "quantity": "5.000"},
        headers=staff_ctx.headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["alert_triggered"] is True
    assert resp.headers.get("X-Alert-Triggered") == "true"


async def test_staff_cannot_register_entry(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    cat = await _create_category(client, admin_ctx.headers)
    loc = await _create_location(client, admin_ctx.headers)
    supply = await _create_supply(client, admin_ctx.headers, cat["id"], loc["id"])

    resp = await client.post(
        f"{API}/movements",
        json={"supply_item_id": supply["id"], "movement_type": "ENTRY", "quantity": "5.000"},
        headers=staff_ctx.headers,
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "MOVEMENT_TYPE_NOT_ALLOWED_FOR_ROLE"


async def test_exit_insufficient_stock_rejected(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    cat = await _create_category(client, admin_ctx.headers)
    loc = await _create_location(client, admin_ctx.headers)
    supply = await _create_supply(
        client, admin_ctx.headers, cat["id"], loc["id"], current="3.000", minimum="10.000"
    )

    resp = await client.post(
        f"{API}/movements",
        json={"supply_item_id": supply["id"], "movement_type": "EXIT", "quantity": "5.000"},
        headers=staff_ctx.headers,
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error_code"] == "INSUFFICIENT_STOCK"
    assert body["available_stock"] == "3.000"


async def test_movement_on_missing_item_not_found(client: AsyncClient, admin_ctx) -> None:
    ghost = "00000000-0000-0000-0000-000000000000"
    resp = await client.post(
        f"{API}/movements",
        json={"supply_item_id": ghost, "movement_type": "ENTRY", "quantity": "5.000"},
        headers=admin_ctx.headers,
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "SUPPLY_ITEM_NOT_FOUND_OR_INACTIVE"
