"""Integración de los módulos avanzados: lotes/FIFO (HU-13), valorización (HU-16),
conciliación (HU-11), dashboard (HU-08), usuarios (HU-10), reportes (HU-12),
producción BOM (HU-15) y gestión de perfil.

Se apoya en las fixtures de conftest (client, *_ctx) contra PostgreSQL y Redis reales.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient

API = "/api/v1"


# ── Helpers ─────────────────────────────────────────────────────────────────

async def _category(client: AsyncClient, headers: dict, name: str = "Lácteos") -> str:
    r = await client.post(
        f"{API}/categories",
        json={"name": name, "color_hex": "#88CCEE"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _location(client: AsyncClient, headers: dict, code: str = "REF-01") -> str:
    r = await client.post(
        f"{API}/locations",
        json={"code": code, "location_type": "REFRIGERATOR"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _supply(
    client: AsyncClient, headers: dict, cat: str, loc: str,
    *, sku: str, current: str = "0.000", minimum: str = "5.000",
) -> str:
    r = await client.post(
        f"{API}/supplies",
        json={
            "name": "Leche Fresca", "sku": sku,
            "category_id": cat, "location_id": loc,
            "unit_of_measure": "L", "current_stock": current,
            "minimum_stock": minimum, "maximum_stock": "1000.000", "unit_cost": "0",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ── Lotes / FIFO / valorización (HU-13, HU-16) ────────────────────────────────

async def test_batch_create_and_fifo_consume(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers)
    sid = await _supply(client, admin_ctx.headers, cat, loc, sku="LECHE-FIFO")

    # Dos lotes: A vence antes (se consume primero), B después.
    a = await client.post(
        f"{API}/supplies/{sid}/batches",
        json={"quantity": "10.00", "batch_code": "L-A",
              "expiration_date": "2026-01-20", "unit_cost": "4.20",
              "vendor_name": "Lácteos Ayacucho"},
        headers=admin_ctx.headers,
    )
    assert a.status_code == 201, a.text
    assert a.json()["new_total_stock"] == "10.000"

    b = await client.post(
        f"{API}/supplies/{sid}/batches",
        json={"quantity": "20.00", "batch_code": "L-B", "expiration_date": "2026-02-10",
              "unit_cost": "4.50"},
        headers=admin_ctx.headers,
    )
    assert b.status_code == 201
    assert b.json()["new_total_stock"] == "30.000"

    # Listado de lotes
    listed = await client.get(f"{API}/supplies/{sid}/batches", headers=admin_ctx.headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 2

    # STAFF consume 15 por FIFO → agota A (10) y toma 5 de B
    consume = await client.post(
        f"{API}/supplies/{sid}/batches/consume",
        json={"supply_item_id": sid, "movement_type": "EXIT", "quantity": "15.00"},
        headers=staff_ctx.headers,
    )
    assert consume.status_code == 201, consume.text
    body = consume.json()
    assert body["new_total_stock"] == "15.000"
    assert len(body["breakdown"]) == 2
    assert body["breakdown"][0]["consumed"] == "10.000"
    assert body["breakdown"][1]["consumed"] == "5.000"

    # Valorización: queda 15 L del lote B a 4.50 = 67.5
    fin = await client.get(f"{API}/dashboard/financials", headers=admin_ctx.headers)
    assert fin.status_code == 200
    assert float(fin.json()["total_active_value"]) == 67.5


async def test_fifo_consume_insufficient_returns_422(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers)
    sid = await _supply(client, admin_ctx.headers, cat, loc, sku="LECHE-POCA")
    await client.post(
        f"{API}/supplies/{sid}/batches",
        json={"quantity": "3.00", "batch_code": "L-X"},
        headers=admin_ctx.headers,
    )
    r = await client.post(
        f"{API}/supplies/{sid}/batches/consume",
        json={"supply_item_id": sid, "movement_type": "EXIT", "quantity": "10.00"},
        headers=staff_ctx.headers,
    )
    assert r.status_code == 422
    assert r.json()["error_code"] == "INSUFFICIENT_STOCK"


# ── Conciliación (HU-11) ──────────────────────────────────────────────────────

async def test_reconciliation_admin_records_adjustment(client: AsyncClient, admin_ctx) -> None:
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers)
    sid = await _supply(client, admin_ctx.headers, cat, loc, sku="MANT-001", current="15.000")

    r = await client.post(
        f"{API}/supplies/reconciliation",
        json={"supply_id": sid, "physical_stock": "13.500", "reason": "Error de digitación"},
        headers=admin_ctx.headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["delta"] == "-1.500"
    assert body["stock_after"] == "13.500"

    # El historial expone el ADJUSTMENT con la razón.
    hist = await client.get(f"{API}/supplies/{sid}/movements", headers=admin_ctx.headers)
    assert hist.status_code == 200
    top = hist.json()["items"][0]
    assert top["movement_type"] == "ADJUSTMENT_SUB"
    assert top["is_adjustment"] is True
    assert top["adjustment_reason"] == "Error de digitación"


async def test_reconciliation_staff_forbidden(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers)
    sid = await _supply(client, admin_ctx.headers, cat, loc, sku="MANT-002", current="10.000")
    r = await client.post(
        f"{API}/supplies/reconciliation",
        json={"supply_id": sid, "physical_stock": "8.000", "reason": "x"},
        headers=staff_ctx.headers,
    )
    assert r.status_code == 403


# ── Dashboard (HU-08 / HU-16) ─────────────────────────────────────────────────

async def test_dashboard_kpis_admin(client: AsyncClient, admin_ctx) -> None:
    r = await client.get(f"{API}/dashboard/kpis", headers=admin_ctx.headers)
    assert r.status_code == 200
    body = r.json()
    assert "total_critical_items" in body
    assert "movements_last_24h" in body
    assert "top_wasted_supplies" in body


async def test_dashboard_kpis_staff_forbidden(client: AsyncClient, staff_ctx) -> None:
    r = await client.get(f"{API}/dashboard/kpis", headers=staff_ctx.headers)
    assert r.status_code == 403


# ── Usuarios (HU-10) ──────────────────────────────────────────────────────────

async def test_user_lifecycle_superadmin(client: AsyncClient, superadmin_ctx) -> None:
    # Crear
    created = await client.post(
        f"{API}/users",
        json={"email": "nuevo@pasteleria.com", "full_name": "Nuevo Staff",
              "password": "Secret@123", "role": "STAFF"},
        headers=superadmin_ctx.headers,
    )
    assert created.status_code == 201, created.text
    uid = created.json()["id"]
    assert "hashed_password" not in created.json()

    # Listar
    listed = await client.get(f"{API}/users", headers=superadmin_ctx.headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 2  # superadmin + nuevo

    # Login del nuevo usuario
    login = await client.post(
        f"{API}/auth/login",
        data={"username": "nuevo@pasteleria.com", "password": "Secret@123"},
    )
    assert login.status_code == 200
    staff_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Antes de suspender, el token del staff funciona
    me = await client.get(f"{API}/auth/me", headers=staff_headers)
    assert me.status_code == 200

    # Suspender → el token queda invalidado (blacklist)
    susp = await client.patch(f"{API}/users/{uid}/suspend", headers=superadmin_ctx.headers)
    assert susp.status_code == 200
    assert susp.json()["is_active"] is False
    blocked = await client.get(f"{API}/auth/me", headers=staff_headers)
    assert blocked.status_code == 401

    # Reactivar
    react = await client.patch(f"{API}/users/{uid}/reactivate", headers=superadmin_ctx.headers)
    assert react.status_code == 200
    assert react.json()["is_active"] is True

    # Restablecer contraseña → la nueva sirve
    reset = await client.patch(
        f"{API}/users/{uid}/password",
        json={"new_password": "Brand@New9"},
        headers=superadmin_ctx.headers,
    )
    assert reset.status_code == 200
    relogin = await client.post(
        f"{API}/auth/login",
        data={"username": "nuevo@pasteleria.com", "password": "Brand@New9"},
    )
    assert relogin.status_code == 200

    # Audit-log
    audit = await client.get(f"{API}/users/{uid}/audit-log", headers=superadmin_ctx.headers)
    assert audit.status_code == 200
    assert "entries" in audit.json()


async def test_user_create_admin_forbidden(client: AsyncClient, admin_ctx) -> None:
    r = await client.post(
        f"{API}/users",
        json={"email": "x@y.com", "full_name": "X Y", "password": "Secret@123", "role": "STAFF"},
        headers=admin_ctx.headers,
    )
    assert r.status_code == 403


async def test_user_duplicate_email_conflict(client: AsyncClient, superadmin_ctx) -> None:
    payload = {"email": "dup@pasteleria.com", "full_name": "Dup", "password": "Secret@123", "role": "STAFF"}
    first = await client.post(f"{API}/users", json=payload, headers=superadmin_ctx.headers)
    assert first.status_code == 201
    second = await client.post(f"{API}/users", json=payload, headers=superadmin_ctx.headers)
    assert second.status_code == 409
    assert second.json()["error_code"] == "USER_EMAIL_ALREADY_EXISTS"


# ── Reportes (HU-12) ──────────────────────────────────────────────────────────

async def test_report_export_admin(client: AsyncClient, admin_ctx) -> None:
    r = await client.get(f"{API}/reports/export?format=csv", headers=admin_ctx.headers)
    assert r.status_code == 200
    assert "attachment" in r.headers.get("content-disposition", "")
    assert r.text.lstrip("﻿").splitlines()[0].startswith("movement_id,timestamp,user_id")


async def test_report_export_staff_forbidden(client: AsyncClient, staff_ctx) -> None:
    r = await client.get(f"{API}/reports/export?format=csv", headers=staff_ctx.headers)
    assert r.status_code == 403


# ── Producción BOM (HU-15) ────────────────────────────────────────────────────

async def _recipe_with_two_ingredients(client, admin_ctx):
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers)
    harina = await _supply(client, admin_ctx.headers, cat, loc, sku="HARINA-P", current="10.000", minimum="0.000")
    leche = await _supply(client, admin_ctx.headers, cat, loc, sku="LECHE-P", current="20.000", minimum="0.000")
    r = await client.post(
        f"{API}/recipes",
        json={"name": "Torta Tres Leches", "yield_unit": "UNIT",
              "items": [
                  {"supply_item_id": harina, "quantity_per_unit": "0.50"},
                  {"supply_item_id": leche, "quantity_per_unit": "1.00"},
              ]},
        headers=admin_ctx.headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"], harina, leche


async def test_production_simulate_and_produce(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    rid, _, _ = await _recipe_with_two_ingredients(client, admin_ctx)

    # Dry-run viable para 10 unidades (need 5 harina, 10 leche)
    sim = await client.post(
        f"{API}/production/simulate",
        json={"recipe_id": rid, "quantity": 10},
        headers=staff_ctx.headers,
    )
    assert sim.status_code == 200, sim.text
    assert sim.json()["feasible"] is True

    # Producir realmente
    prod = await client.post(
        f"{API}/production/produce",
        json={"recipe_id": rid, "quantity": 10},
        headers=staff_ctx.headers,
    )
    assert prod.status_code == 201, prod.text
    assert prod.json()["quantity_produced"] == 10
    assert len(prod.json()["ingredients"]) == 2


async def test_production_simulate_returns_pick_list(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    """El simulacro devuelve la lista de preparación: ubicación + desglose FIFO por lote."""
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers, code="REF-07")
    harina = await _supply(
        client, admin_ctx.headers, cat, loc, sku="HARINA-PICK", current="0.000", minimum="0.000"
    )
    # Dos lotes FIFO: L-A vence antes → se agota primero.
    for code, qty, exp in [("L-A", "12.00", "2026-08-01"), ("L-B", "18.00", "2026-09-01")]:
        r = await client.post(
            f"{API}/supplies/{harina}/batches",
            json={"quantity": qty, "batch_code": code, "expiration_date": exp, "unit_cost": "3.0"},
            headers=admin_ctx.headers,
        )
        assert r.status_code == 201, r.text

    recipe = await client.post(
        f"{API}/recipes",
        json={"name": "Pan Rústico", "yield_unit": "UNIT",
              "items": [{"supply_item_id": harina, "quantity_per_unit": "2.00"}]},
        headers=admin_ctx.headers,
    )
    assert recipe.status_code == 201, recipe.text
    rid = recipe.json()["id"]

    # 10 unidades → 20 kg: 12 del lote que vence antes + 8 del segundo.
    sim = await client.post(
        f"{API}/production/simulate",
        json={"recipe_id": rid, "quantity": 10},
        headers=staff_ctx.headers,
    )
    assert sim.status_code == 200, sim.text
    ing = sim.json()["ingredients"][0]
    assert ing["location_code"] == "REF-07"
    assert ing["unit"] == "L"
    plan = [(p["batch_code"], p["take"]) for p in ing["batch_plan"]]
    assert plan == [("L-A", "12.000"), ("L-B", "8.000")]


async def test_production_preparation_snapshot(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    """Tras producir, el historial expone la lista de preparación usada (snapshot)."""
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers, code="REF-08")
    harina = await _supply(
        client, admin_ctx.headers, cat, loc, sku="HARINA-SNAP", current="0.000", minimum="0.000"
    )
    for code, qty, exp in [("S-A", "12.00", "2026-08-01"), ("S-B", "18.00", "2026-09-01")]:
        r = await client.post(
            f"{API}/supplies/{harina}/batches",
            json={"quantity": qty, "batch_code": code, "expiration_date": exp, "unit_cost": "3.0"},
            headers=admin_ctx.headers,
        )
        assert r.status_code == 201, r.text

    recipe = await client.post(
        f"{API}/recipes",
        json={"name": "Pan Snapshot", "yield_unit": "UNIT",
              "items": [{"supply_item_id": harina, "quantity_per_unit": "2.00"}]},
        headers=admin_ctx.headers,
    )
    assert recipe.status_code == 201, recipe.text
    rid = recipe.json()["id"]

    prod = await client.post(
        f"{API}/production/produce",
        json={"recipe_id": rid, "quantity": 10},   # 20 kg: 12 de S-A + 8 de S-B
        headers=staff_ctx.headers,
    )
    assert prod.status_code == 201, prod.text
    pid = prod.json()["production_id"]

    prep = await client.get(
        f"{API}/production/{pid}/preparation", headers=admin_ctx.headers
    )
    assert prep.status_code == 200, prep.text
    body = prep.json()
    assert body["recipe_name"] == "Pan Snapshot"
    assert len(body["ingredients"]) == 1
    ing = body["ingredients"][0]
    assert ing["supply_name"] == "Leche Fresca"
    assert ing["unit"] == "L"
    assert ing["location_code"] == "REF-08"
    assert ing["quantity_consumed"] == "20.000"
    batches = [(b["batch_code"], b["quantity"]) for b in ing["batches"]]
    assert batches == [("S-A", "12.000"), ("S-B", "8.000")]


async def test_production_preparation_not_found(client: AsyncClient, admin_ctx) -> None:
    ghost = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"{API}/production/{ghost}/preparation", headers=admin_ctx.headers)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "PRODUCTION_RUN_NOT_FOUND"


async def test_production_preparation_staff_forbidden(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    ghost = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"{API}/production/{ghost}/preparation", headers=staff_ctx.headers)
    assert resp.status_code == 403


async def test_production_rollback_on_shortage(client: AsyncClient, admin_ctx, staff_ctx) -> None:
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers)
    harina = await _supply(client, admin_ctx.headers, cat, loc, sku="HARINA-Q", current="10.000", minimum="0.000")
    leche = await _supply(client, admin_ctx.headers, cat, loc, sku="LECHE-Q", current="4.000", minimum="0.000")
    r = await client.post(
        f"{API}/recipes",
        json={"name": "Torta Escasa", "yield_unit": "UNIT",
              "items": [
                  {"supply_item_id": harina, "quantity_per_unit": "0.50"},
                  {"supply_item_id": leche, "quantity_per_unit": "1.00"},
              ]},
        headers=admin_ctx.headers,
    )
    rid = r.json()["id"]

    # Simular NO viable
    sim = await client.post(
        f"{API}/production/simulate",
        json={"recipe_id": rid, "quantity": 10},
        headers=staff_ctx.headers,
    )
    assert sim.json()["feasible"] is False

    # Producir → rollback 422, la harina no se descuenta
    prod = await client.post(
        f"{API}/production/produce",
        json={"recipe_id": rid, "quantity": 10},
        headers=staff_ctx.headers,
    )
    assert prod.status_code == 422
    assert prod.json()["error_code"] == "RECIPE_PRODUCTION_FAILED_STOCK_SHORTAGE"

    # La harina sigue intacta (no hubo movimientos)
    hist = await client.get(f"{API}/supplies/{harina}/movements", headers=admin_ctx.headers)
    assert hist.json()["total"] == 0


# ── Producto terminado y registro de producción (HU-17) ───────────────────────

async def test_production_registers_finished_product_stock_and_history(
    client: AsyncClient, admin_ctx, staff_ctx
) -> None:
    """SC-HU17-01/02: la receta auto-crea el producto; producir sube su stock e historial."""
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers)
    harina = await _supply(
        client, admin_ctx.headers, cat, loc, sku="HARINA-FIN",
        current="10.000", minimum="0.000",
    )

    # La receta define el producto terminado → se crea solo (no se registra aparte)
    recipe = await client.post(
        f"{API}/recipes",
        json={
            "name": "Torta de Chocolate", "yield_unit": "UNIT",
            "product_name": "Torta de Chocolate", "product_location_id": loc,
            "shelf_life_days": 4,
            "items": [{"supply_item_id": harina, "quantity_per_unit": "0.50"}],
        },
        headers=admin_ctx.headers,
    )
    assert recipe.status_code == 201, recipe.text
    rid = recipe.json()["id"]
    product_id = recipe.json()["produces_supply_item_id"]
    assert product_id is not None

    # El producto aparece en la sección de productos terminados, no en insumos
    prods = await client.get(
        f"{API}/supplies?item_type=FINISHED_PRODUCT", headers=admin_ctx.headers
    )
    assert any(s["id"] == product_id for s in prods.json()["items"])
    ings = await client.get(
        f"{API}/supplies?item_type=INGREDIENT", headers=admin_ctx.headers
    )
    assert all(s["id"] != product_id for s in ings.json()["items"])

    # STAFF produce 10 unidades
    prod = await client.post(
        f"{API}/production/produce",
        json={"recipe_id": rid, "quantity": 10},
        headers=staff_ctx.headers,
    )
    assert prod.status_code == 201, prod.text
    body = prod.json()
    assert body["product_supply_item_id"] == product_id
    assert body["production_id"] is not None
    assert Decimal(body["product_new_stock"]) == Decimal("10.000")

    # El stock del producto terminado subió a 10 en la BD
    supplies = await client.get(
        f"{API}/supplies?item_type=FINISHED_PRODUCT", headers=admin_ctx.headers
    )
    torta = next(s for s in supplies.json()["items"] if s["id"] == product_id)
    assert Decimal(torta["current_stock"]) == Decimal("10.000")

    # La corrida quedó en el historial de producción
    history = await client.get(f"{API}/production/history", headers=admin_ctx.headers)
    assert history.status_code == 200, history.text
    assert history.json()["total"] >= 1
    run = history.json()["items"][0]
    assert run["recipe_name"] == "Torta de Chocolate"
    assert run["product_name"] == "Torta de Chocolate"
    assert Decimal(run["quantity_produced"]) == Decimal("10.000")

    # STAFF no puede ver el historial global (ADMIN+)
    forbidden = await client.get(f"{API}/production/history", headers=staff_ctx.headers)
    assert forbidden.status_code == 403


# ── Perfil (self-service) ─────────────────────────────────────────────────────

async def test_profile_update_name(client: AsyncClient, admin_ctx) -> None:
    r = await client.patch(
        f"{API}/auth/me",
        json={"full_name": "Nombre Actualizado"},
        headers=admin_ctx.headers,
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Nombre Actualizado"


async def test_profile_avatar_upload(client: AsyncClient, admin_ctx) -> None:
    import base64
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMCAoK5f4mZAAAAAElFTkSuQmCC"
    )
    # Formato válido → 200 y avatar_url servible bajo /static
    ok = await client.post(
        f"{API}/auth/me/avatar",
        files={"file": ("px.png", png, "image/png")},
        headers=admin_ctx.headers,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["avatar_url"].startswith("/static/avatars/")

    # Formato inválido → 422
    bad = await client.post(
        f"{API}/auth/me/avatar",
        files={"file": ("x.txt", b"hola", "text/plain")},
        headers=admin_ctx.headers,
    )
    assert bad.status_code == 422


async def test_profile_change_password(client: AsyncClient, admin_ctx) -> None:
    # Clave actual incorrecta → 401
    bad = await client.patch(
        f"{API}/auth/me/password",
        json={"current_password": "no-es", "new_password": "Otra@Clave1"},
        headers=admin_ctx.headers,
    )
    assert bad.status_code == 401

    # Clave actual correcta → 200 y la nueva permite login
    ok = await client.patch(
        f"{API}/auth/me/password",
        json={"current_password": admin_ctx.password, "new_password": "Otra@Clave1"},
        headers=admin_ctx.headers,
    )
    assert ok.status_code == 200
    login = await client.post(
        f"{API}/auth/login",
        data={"username": admin_ctx.email, "password": "Otra@Clave1"},
    )
    assert login.status_code == 200


# ── Paginación + cache de insumos (HU-06) ─────────────────────────────────────

async def test_supplies_pagination_cache_header(client: AsyncClient, admin_ctx) -> None:
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers)
    await _supply(client, admin_ctx.headers, cat, loc, sku="PAG-1", current="5.000")

    first = await client.get(f"{API}/supplies?page=1&limit=20", headers=admin_ctx.headers)
    assert first.status_code == 200
    assert first.headers.get("X-Cache") == "MISS"

    second = await client.get(f"{API}/supplies?page=1&limit=20", headers=admin_ctx.headers)
    assert second.headers.get("X-Cache") == "HIT"


# ── Íconos permitidos de categoría ────────────────────────────────────────────

async def test_category_rejects_unlisted_icon(client: AsyncClient, admin_ctx) -> None:
    r = await client.post(
        f"{API}/categories",
        json={"name": "Colorantes", "color_hex": "#FF6B9D", "icon_name": "palette"},
        headers=admin_ctx.headers,
    )
    assert r.status_code == 422, r.text


async def test_category_accepts_listed_icon(client: AsyncClient, admin_ctx) -> None:
    r = await client.post(
        f"{API}/categories",
        json={"name": "Chocolatería", "color_hex": "#6B4226", "icon_name": "cake"},
        headers=admin_ctx.headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["icon_name"] == "cake"


# ── Ajustes del sistema (nombre, logo, tema) ──────────────────────────────────

async def test_settings_readable_without_authentication(client: AsyncClient) -> None:
    """El login necesita la marca antes de que exista una sesión."""
    r = await client.get(f"{API}/settings")
    assert r.status_code == 200
    body = r.json()
    assert body["app_name"]
    assert body["theme"] in {"rosa", "chocolate", "menta", "azul"}


async def test_settings_update_requires_superadmin(
    client: AsyncClient, admin_ctx, staff_ctx
) -> None:
    for ctx in (admin_ctx, staff_ctx):
        r = await client.patch(
            f"{API}/settings", json={"theme": "azul"}, headers=ctx.headers
        )
        assert r.status_code == 403, f"{ctx.email}: {r.text}"


async def test_settings_update_by_superadmin(client: AsyncClient, superadmin_ctx) -> None:
    r = await client.patch(
        f"{API}/settings",
        json={"app_name": "Dulce Ayacucho", "theme": "chocolate"},
        headers=superadmin_ctx.headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["app_name"] == "Dulce Ayacucho"
    assert r.json()["theme"] == "chocolate"

    # La lectura pública refleja el cambio (la caché se invalida al guardar).
    public = await client.get(f"{API}/settings")
    assert public.json()["theme"] == "chocolate"


async def test_settings_rejects_unknown_theme(client: AsyncClient, superadmin_ctx) -> None:
    r = await client.patch(
        f"{API}/settings", json={"theme": "morado"}, headers=superadmin_ctx.headers
    )
    assert r.status_code == 422, r.text


# ── Logo: normalización 1:1 y validación real de la imagen ────────────────────

def _png_bytes(width: int, height: int, color: str = "#2563EB") -> bytes:
    from io import BytesIO
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, format="PNG")
    return buffer.getvalue()


async def _upload_logo(client: AsyncClient, headers: dict, content: bytes, ctype: str):
    return await client.post(
        f"{API}/settings/logo",
        files={"file": ("logo.png", content, ctype)},
        headers=headers,
    )


async def test_logo_rectangular_is_normalized_to_square(
    client: AsyncClient, superadmin_ctx
) -> None:
    from pathlib import Path
    from PIL import Image

    r = await _upload_logo(
        client, superadmin_ctx.headers, _png_bytes(600, 200), "image/png"
    )
    assert r.status_code == 200, r.text

    saved = Path(r.json()["logo_url"].lstrip("/"))
    assert saved.exists(), saved
    with Image.open(saved) as img:
        assert img.size[0] == img.size[1], f"el logo no es 1:1: {img.size}"
    saved.unlink()


async def test_logo_rejects_non_image_with_image_content_type(
    client: AsyncClient, superadmin_ctx
) -> None:
    """El content-type lo declara el cliente: decodificar es lo que lo prueba."""
    r = await _upload_logo(
        client, superadmin_ctx.headers, b"<?php system($_GET['c']); ?>", "image/png"
    )
    assert r.status_code == 422, r.text


async def test_logo_rejects_disallowed_content_type(
    client: AsyncClient, superadmin_ctx
) -> None:
    r = await _upload_logo(client, superadmin_ctx.headers, _png_bytes(64, 64), "text/plain")
    assert r.status_code == 422, r.text


async def test_logo_upload_requires_superadmin(client: AsyncClient, admin_ctx) -> None:
    r = await _upload_logo(client, admin_ctx.headers, _png_bytes(64, 64), "image/png")
    assert r.status_code == 403, r.text


# ── Fondos del login por dispositivo ──────────────────────────────────────────

_EXPECTED_BG_SIZE = {"mobile": (720, 1280), "tablet": (900, 1200), "desktop": (1920, 1080)}


async def _upload_background(client: AsyncClient, headers: dict, device: str, content: bytes):
    return await client.post(
        f"{API}/settings/login-background/{device}",
        files={"file": ("bg.png", content, "image/png")},
        headers=headers,
    )


async def test_login_background_is_fitted_per_device(
    client: AsyncClient, superadmin_ctx
) -> None:
    from pathlib import Path
    from PIL import Image

    for device, size in _EXPECTED_BG_SIZE.items():
        r = await _upload_background(
            client, superadmin_ctx.headers, device, _png_bytes(1000, 1000)
        )
        assert r.status_code == 200, r.text

        url = r.json()[f"login_bg_{device}_url"]
        saved = Path(url.lstrip("/"))
        assert saved.exists(), saved
        with Image.open(saved) as img:
            assert img.size == size, f"{device}: {img.size} != {size}"
            assert img.format == "JPEG"
        saved.unlink()


async def test_login_background_replacement_deletes_previous_file(
    client: AsyncClient, superadmin_ctx
) -> None:
    """Sin esto, cada reemplazo dejaría el archivo anterior huérfano en disco."""
    from pathlib import Path

    first = await _upload_background(
        client, superadmin_ctx.headers, "desktop", _png_bytes(1000, 1000)
    )
    old = Path(first.json()["login_bg_desktop_url"].lstrip("/"))
    assert old.exists()

    second = await _upload_background(
        client, superadmin_ctx.headers, "desktop", _png_bytes(1000, 1000, "#0F9D76")
    )
    new = Path(second.json()["login_bg_desktop_url"].lstrip("/"))
    assert new.exists()
    assert not old.exists(), "el archivo reemplazado sigue en disco"
    new.unlink()


async def test_login_background_delete_clears_field(
    client: AsyncClient, superadmin_ctx
) -> None:
    from pathlib import Path

    up = await _upload_background(
        client, superadmin_ctx.headers, "tablet", _png_bytes(800, 800)
    )
    saved = Path(up.json()["login_bg_tablet_url"].lstrip("/"))
    assert saved.exists()

    r = await client.delete(
        f"{API}/settings/login-background/tablet", headers=superadmin_ctx.headers
    )
    assert r.status_code == 200, r.text
    assert r.json()["login_bg_tablet_url"] is None
    assert not saved.exists()


async def test_login_background_rejects_unknown_device(
    client: AsyncClient, superadmin_ctx
) -> None:
    r = await _upload_background(
        client, superadmin_ctx.headers, "smartwatch", _png_bytes(64, 64)
    )
    assert r.status_code == 422, r.text


async def test_login_background_requires_superadmin(client: AsyncClient, admin_ctx) -> None:
    r = await _upload_background(client, admin_ctx.headers, "desktop", _png_bytes(64, 64))
    assert r.status_code == 403, r.text


# ── Paginación de la auditoría (HU-10-03) ─────────────────────────────────────

async def test_audit_log_paginates_without_losing_entries(
    client: AsyncClient, superadmin_ctx, admin_ctx
) -> None:
    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers)
    for i in range(5):
        await _supply(client, admin_ctx.headers, cat, loc, sku=f"AUD-{i}", current="10.000")

    full = await client.get(
        f"{API}/users/{admin_ctx.user_id}/audit-log", headers=superadmin_ctx.headers
    )
    assert full.status_code == 200, full.text
    total = full.json()["total"]
    assert total >= 2

    seen: list[str] = []
    for page in (1, 2):
        r = await client.get(
            f"{API}/users/{admin_ctx.user_id}/audit-log?page={page}&limit=1",
            headers=superadmin_ctx.headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["page"] == page
        assert body["limit"] == 1
        assert body["total"] == total, "el total debe ser el global, no el de la página"
        assert len(body["entries"]) == 1
        seen.append(body["entries"][0]["entity_id"])

    assert seen[0] != seen[1], "las páginas devuelven la misma entrada"


async def test_audit_log_page_beyond_range_is_empty_not_error(
    client: AsyncClient, superadmin_ctx
) -> None:
    r = await client.get(
        f"{API}/users/{superadmin_ctx.user_id}/audit-log?page=999",
        headers=superadmin_ctx.headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["entries"] == []


async def test_audit_log_rejects_oversized_limit(
    client: AsyncClient, superadmin_ctx
) -> None:
    r = await client.get(
        f"{API}/users/{superadmin_ctx.user_id}/audit-log?limit=999",
        headers=superadmin_ctx.headers,
    )
    assert r.status_code == 422


# ── Reglas de negocio en Ajustes ──────────────────────────────────────────────

async def test_settings_business_rules_roundtrip(client: AsyncClient, superadmin_ctx) -> None:
    r = await client.patch(
        f"{API}/settings",
        json={
            "expiration_alert_days": 12,
            "currency_code": "USD",
            "locale": "en-US",
            "page_size": 30,
            "login_overlay_opacity": 65,
            "business_name": "Dulce Tentación EIRL",
            "tax_id": "20512345678",
        },
        headers=superadmin_ctx.headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["expiration_alert_days"] == 12
    assert body["currency_code"] == "USD"
    assert body["page_size"] == 30
    assert body["login_overlay_opacity"] == 65
    assert body["business_name"] == "Dulce Tentación EIRL"


async def test_settings_blank_string_clears_optional_field(
    client: AsyncClient, superadmin_ctx
) -> None:
    """La cadena vacía borra; el None significa «no tocar»."""
    await client.patch(
        f"{API}/settings",
        json={"tax_id": "20512345678", "address": "Jr. Lima 123"},
        headers=superadmin_ctx.headers,
    )
    r = await client.patch(
        f"{API}/settings", json={"tax_id": ""}, headers=superadmin_ctx.headers
    )
    assert r.status_code == 200, r.text
    assert r.json()["tax_id"] is None
    assert r.json()["address"] == "Jr. Lima 123", "un campo no enviado no debe borrarse"


@pytest.mark.parametrize(
    "payload",
    [
        {"expiration_alert_days": 0},
        {"expiration_alert_days": 91},
        {"page_size": 4},
        {"page_size": 101},
        {"login_overlay_opacity": 81},
        {"currency_code": "pen"},
        {"currency_code": "SOLES"},
        {"locale": "es_PE"},
    ],
)
async def test_settings_rejects_out_of_range(
    client: AsyncClient, superadmin_ctx, payload
) -> None:
    r = await client.patch(f"{API}/settings", json=payload, headers=superadmin_ctx.headers)
    assert r.status_code == 422, f"{payload}: {r.text}"


async def test_avatar_is_normalized_to_square(client: AsyncClient, admin_ctx) -> None:
    """El menú lo muestra en un círculo: una foto rectangular saldría estirada."""
    from pathlib import Path
    from PIL import Image

    r = await client.post(
        f"{API}/auth/me/avatar",
        files={"file": ("me.png", _png_bytes(600, 200), "image/png")},
        headers=admin_ctx.headers,
    )
    assert r.status_code == 200, r.text

    saved = Path(r.json()["avatar_url"].lstrip("/"))
    assert saved.exists()
    with Image.open(saved) as img:
        assert img.size[0] == img.size[1], f"avatar no cuadrado: {img.size}"
    saved.unlink()


async def test_expiration_scan_uses_configured_threshold(
    client: AsyncClient, superadmin_ctx, admin_ctx, db_sessionmaker, test_redis
) -> None:
    """El umbral sale de Ajustes, no de una variable de entorno."""
    from datetime import date, timedelta

    from app.application.services.alert_service import AlertService
    from app.application.services.batch_service import BatchService
    from app.infrastructure.repositories.batch_repository import BatchRepository
    from app.infrastructure.repositories.movement_repository import MovementRepository
    from app.infrastructure.repositories.supply_repository import SupplyRepository

    cat = await _category(client, admin_ctx.headers)
    loc = await _location(client, admin_ctx.headers)
    supply = await _supply(client, admin_ctx.headers, cat, loc, sku="EXP-1", current="0.000")

    far = (date.today() + timedelta(days=20)).isoformat()
    r = await client.post(
        f"{API}/supplies/{supply}/batches",
        json={"batch_code": "L-FAR", "quantity": "5.000", "unit_cost": "1.0000",
              "expiration_date": far},
        headers=admin_ctx.headers,
    )
    assert r.status_code in (200, 201), r.text

    async with db_sessionmaker() as session:
        service = BatchService(
            supply_repo=SupplyRepository(session),
            batch_repo=BatchRepository(session),
            movement_repo=MovementRepository(session),
            alert_service=AlertService(redis=test_redis),
            redis=test_redis,
        )
        assert await service.scan_expiring_batches(alert_days=5) == 0
        assert await service.scan_expiring_batches(alert_days=30) == 1
