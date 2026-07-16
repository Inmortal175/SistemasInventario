"""HU-15: producción por recetas (BOM) con validación total y rollback atómico."""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.services.alert_service import AlertService
from app.application.services.production_service import ProductionService
from app.domain.enums import LocationType, UnitMeasure
from app.domain.exceptions import RecipeProductionShortageError


def _recipe_item(supply_id, qpu):
    ri = MagicMock()
    ri.supply_item_id = supply_id
    ri.quantity_per_unit = Decimal(qpu)
    return ri


def _supply(name, stock, minimum="0", cost="1.0"):
    s = MagicMock()
    s.id = uuid.uuid4()
    s.name = name
    s.current_stock = Decimal(stock)
    s.minimum_stock = Decimal(minimum)
    s.unit_cost = Decimal(cost)
    s.unit_of_measure = UnitMeasure.KG
    s.location_id = uuid.uuid4()
    return s


def _location(code="EST-01", location_type=LocationType.SHELF):
    loc = MagicMock()
    loc.code = code
    loc.location_type = location_type
    return loc


def _location_repo(code="EST-01"):
    """Repo de ubicaciones que resuelve cualquier id a una ubicación con `code`."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=_location(code=code))
    return repo


def _batch(code, stock, expiration=None):
    b = MagicMock()
    b.batch_code = code
    b.current_stock = Decimal(stock)
    b.expiration_date = expiration
    return b


def _batch_repo(fifo=None):
    """Repo de lotes con la lista FIFO de solo lectura ya configurada."""
    repo = AsyncMock()
    repo.list_active_fifo = AsyncMock(return_value=list(fifo or []))
    return repo


@pytest.mark.asyncio
async def test_production_aborts_when_one_ingredient_short(mock_redis):
    """SC-HU15-02: falta Leche → RecipeProductionShortageError, sin descontar Harina."""
    harina = _supply("Harina de Trigo", "10.00")
    leche = _supply("Leche Fresca", "4.00")

    recipe = MagicMock()
    recipe.id = uuid.uuid4()
    recipe.name = "Torta Tres Leches"
    recipe.items = [
        _recipe_item(harina.id, "0.50"),   # need 5.00 (ok)
        _recipe_item(leche.id, "1.00"),    # need 10.00 (falta: 4.00)
    ]

    recipe_repo = AsyncMock()
    recipe_repo.get_with_items = AsyncMock(return_value=recipe)
    supply_repo = AsyncMock()
    supply_repo.get_by_id_for_update = AsyncMock(side_effect=lambda sid: (
        harina if sid == harina.id else leche
    ))
    supply_repo.update_stock = AsyncMock()
    batch_repo = AsyncMock()
    movement_repo = AsyncMock()

    service = ProductionService(
        recipe_repo=recipe_repo,
        supply_repo=supply_repo,
        batch_repo=batch_repo,
        movement_repo=movement_repo,
        production_run_repo=AsyncMock(),
        category_repo=AsyncMock(),
        location_repo=AsyncMock(),
        alert_service=AlertService(redis=mock_redis),
        redis=mock_redis,
    )

    with pytest.raises(RecipeProductionShortageError) as exc:
        await service.produce(
            recipe_id=recipe.id, quantity=10, performed_by_id=uuid.uuid4()
        )

    assert exc.value.supply_id == str(leche.id)
    assert exc.value.required == Decimal("10.00")
    assert exc.value.available == Decimal("4.00")
    # Ningún insumo fue descontado: la validación ocurre antes del descuento.
    supply_repo.update_stock.assert_not_awaited()
    movement_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_simulate_is_readonly_and_reports_deficit(mock_redis):
    """Dry-run: no descuenta stock y reporta el déficit del ingrediente faltante."""
    harina = _supply("Harina de Trigo", "10.00")
    leche = _supply("Leche Fresca", "4.00")

    recipe = MagicMock()
    recipe.id = uuid.uuid4()
    recipe.name = "Torta Tres Leches"
    recipe.items = [
        _recipe_item(harina.id, "0.50"),   # need 5.00 (ok)
        _recipe_item(leche.id, "1.00"),    # need 10.00 (falta 6.00)
    ]

    recipe_repo = AsyncMock()
    recipe_repo.get_with_items = AsyncMock(return_value=recipe)
    supply_repo = AsyncMock()
    supply_repo.get_by_id = AsyncMock(side_effect=lambda sid: (
        harina if sid == harina.id else leche
    ))
    supply_repo.update_stock = AsyncMock()
    supply_repo.get_by_id_for_update = AsyncMock()
    movement_repo = AsyncMock()

    service = ProductionService(
        recipe_repo=recipe_repo,
        supply_repo=supply_repo,
        batch_repo=_batch_repo(),
        movement_repo=movement_repo,
        production_run_repo=AsyncMock(),
        category_repo=AsyncMock(),
        location_repo=_location_repo(),
        alert_service=AlertService(redis=mock_redis),
        redis=mock_redis,
    )

    result = await service.simulate(recipe_id=recipe.id, quantity=10)

    assert result.feasible is False
    assert len(result.ingredients) == 2
    assert len(result.missing) == 1
    assert result.missing[0].supply_id == leche.id
    assert result.missing[0].required == Decimal("10.00")
    assert result.missing[0].available == Decimal("4.00")
    assert result.missing[0].deficit == Decimal("6.00")
    # Es de solo lectura: no bloquea filas, no descuenta, no crea movimientos.
    supply_repo.get_by_id_for_update.assert_not_awaited()
    supply_repo.update_stock.assert_not_awaited()
    movement_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_simulate_feasible_when_enough_stock(mock_redis):
    """Dry-run viable: feasible=True y sin faltantes."""
    harina = _supply("Harina", "10.00")
    recipe = MagicMock()
    recipe.id = uuid.uuid4()
    recipe.name = "Pan"
    recipe.items = [_recipe_item(harina.id, "0.50")]   # need 2.50 para 5 uds

    recipe_repo = AsyncMock()
    recipe_repo.get_with_items = AsyncMock(return_value=recipe)
    supply_repo = AsyncMock()
    supply_repo.get_by_id = AsyncMock(return_value=harina)

    service = ProductionService(
        recipe_repo=recipe_repo,
        supply_repo=supply_repo,
        batch_repo=_batch_repo(),
        movement_repo=AsyncMock(),
        production_run_repo=AsyncMock(),
        category_repo=AsyncMock(),
        location_repo=_location_repo(),
        alert_service=AlertService(redis=mock_redis),
        redis=mock_redis,
    )
    result = await service.simulate(recipe_id=recipe.id, quantity=5)
    assert result.feasible is True
    assert result.missing == []
    assert result.ingredients[0].required == Decimal("2.50")


@pytest.mark.asyncio
async def test_simulate_builds_pick_plan_with_location_and_fifo(mock_redis):
    """Lista de preparación: ubicación del insumo + desglose FIFO de lotes a extraer."""
    from datetime import date

    harina = _supply("Harina", "30.00")
    recipe = MagicMock()
    recipe.id = uuid.uuid4()
    recipe.name = "Pan"
    recipe.items = [_recipe_item(harina.id, "2.00")]   # need 20.00 para 10 uds

    recipe_repo = AsyncMock()
    recipe_repo.get_with_items = AsyncMock(return_value=recipe)
    supply_repo = AsyncMock()
    supply_repo.get_by_id = AsyncMock(return_value=harina)

    # Dos lotes FIFO: el que vence antes se agota primero, el resto sale del segundo.
    lotes = [
        _batch("L-A", "12.00", expiration=date(2026, 8, 1)),
        _batch("L-B", "18.00", expiration=date(2026, 9, 1)),
    ]

    service = ProductionService(
        recipe_repo=recipe_repo,
        supply_repo=supply_repo,
        batch_repo=_batch_repo(lotes),
        movement_repo=AsyncMock(),
        production_run_repo=AsyncMock(),
        category_repo=AsyncMock(),
        location_repo=_location_repo(code="EST-03"),
        alert_service=AlertService(redis=mock_redis),
        redis=mock_redis,
    )

    result = await service.simulate(recipe_id=recipe.id, quantity=10)

    ing = result.ingredients[0]
    assert ing.location_code == "EST-03"
    assert ing.unit == UnitMeasure.KG
    # 20 requeridos: 12 del primer lote (FIFO) + 8 del segundo.
    assert [(p.batch_code, p.take) for p in ing.batch_plan] == [
        ("L-A", Decimal("12.00")),
        ("L-B", Decimal("8.00")),
    ]
    # No se descuenta nada del simulacro.
    supply_repo.update_stock.assert_not_awaited()


@pytest.mark.asyncio
async def test_production_success_deducts_all_ingredients(mock_redis):
    """SC-HU15-01: stock suficiente → descuenta todos y registra un movimiento por insumo."""
    harina = _supply("Harina de Trigo", "10.00", cost="2.0")
    leche = _supply("Leche Fresca", "20.00", cost="3.0")

    recipe = MagicMock()
    recipe.id = uuid.uuid4()
    recipe.name = "Torta Tres Leches"
    # Receta sin producto terminado asociado (semántica HU-15 pura).
    recipe.produces_supply_item_id = None
    recipe.shelf_life_days = None
    recipe.items = [
        _recipe_item(harina.id, "0.50"),   # need 5.00
        _recipe_item(leche.id, "1.00"),    # need 10.00
    ]

    recipe_repo = AsyncMock()
    recipe_repo.get_with_items = AsyncMock(return_value=recipe)
    supply_repo = AsyncMock()
    supply_repo.get_by_id_for_update = AsyncMock(side_effect=lambda sid: (
        harina if sid == harina.id else leche
    ))
    supply_repo.update_stock = AsyncMock()
    batch_repo = AsyncMock()
    # Sin lotes → descuento directo del stock del insumo
    batch_repo.list_active_fifo_for_update = AsyncMock(return_value=[])
    batch_repo.list_active_by_supply = AsyncMock(return_value=[])
    batch_repo.sum_active_stock = AsyncMock(return_value=Decimal("0"))
    movement_repo = AsyncMock()
    mv = MagicMock()
    mv.id = uuid.uuid4()
    movement_repo.create = AsyncMock(return_value=mv)

    run = MagicMock()
    run.id = uuid.uuid4()
    production_run_repo = AsyncMock()
    production_run_repo.create = AsyncMock(return_value=run)

    service = ProductionService(
        recipe_repo=recipe_repo,
        supply_repo=supply_repo,
        batch_repo=batch_repo,
        movement_repo=movement_repo,
        production_run_repo=production_run_repo,
        category_repo=AsyncMock(),
        location_repo=AsyncMock(),
        alert_service=AlertService(redis=mock_redis),
        redis=mock_redis,
    )

    result = await service.produce(
        recipe_id=recipe.id, quantity=10, performed_by_id=uuid.uuid4()
    )

    assert result.quantity_produced == 10
    assert len(result.ingredients) == 2
    assert supply_repo.update_stock.await_count == 2
    assert movement_repo.create.await_count == 2


@pytest.mark.asyncio
async def test_production_registers_finished_product_and_run(mock_redis):
    """SC-HU17-01: producir suma stock al producto terminado y asienta la corrida."""
    harina = _supply("Harina de Trigo", "10.00", cost="2.0")
    producto = _supply("Torta de Chocolate", "0")   # producto terminado, stock inicial 0

    recipe = MagicMock()
    recipe.id = uuid.uuid4()
    recipe.name = "Torta de Chocolate"
    recipe.produces_supply_item_id = producto.id
    recipe.shelf_life_days = 4
    recipe.items = [_recipe_item(harina.id, "0.50")]   # need 5.00 para 10 uds

    recipe_repo = AsyncMock()
    recipe_repo.get_with_items = AsyncMock(return_value=recipe)
    supply_repo = AsyncMock()
    supply_repo.get_by_id_for_update = AsyncMock(side_effect=lambda sid: (
        harina if sid == harina.id else producto
    ))
    supply_repo.update_stock = AsyncMock()

    batch_repo = AsyncMock()
    batch_repo.list_active_fifo_for_update = AsyncMock(return_value=[])   # harina sin lotes
    batch_repo.list_active_by_supply = AsyncMock(return_value=[])
    # 0 para harina (fuerza el fallback directo); 10 para el producto tras crear su lote
    batch_repo.sum_active_stock = AsyncMock(
        side_effect=lambda sid: (Decimal("10") if sid == producto.id else Decimal("0"))
    )
    batch = MagicMock()
    batch.id = uuid.uuid4()
    batch_repo.create = AsyncMock(return_value=batch)

    movement_repo = AsyncMock()
    mv = MagicMock()
    mv.id = uuid.uuid4()
    movement_repo.create = AsyncMock(return_value=mv)

    run = MagicMock()
    run.id = uuid.uuid4()
    production_run_repo = AsyncMock()
    production_run_repo.create = AsyncMock(return_value=run)

    service = ProductionService(
        recipe_repo=recipe_repo,
        supply_repo=supply_repo,
        batch_repo=batch_repo,
        movement_repo=movement_repo,
        production_run_repo=production_run_repo,
        category_repo=AsyncMock(),
        location_repo=AsyncMock(),
        alert_service=AlertService(redis=mock_redis),
        redis=mock_redis,
    )

    result = await service.produce(
        recipe_id=recipe.id, quantity=10, performed_by_id=uuid.uuid4()
    )

    # Producto terminado: se creó un lote y se sumó stock (EXIT harina + ENTRY producto)
    batch_repo.create.assert_awaited_once()
    assert movement_repo.create.await_count == 2
    assert result.product_supply_item_id == producto.id
    assert result.product_name == "Torta de Chocolate"
    assert result.product_new_stock == Decimal("10")
    assert result.total_ingredient_cost == Decimal("10.00")   # 5.00 × 2.0
    # La corrida quedó registrada
    production_run_repo.create.assert_awaited_once()
    assert result.production_id == run.id
    # Snapshot de preparación: 1 insumo consumido → 1 asiento de run item.
    production_run_repo.add_item.assert_awaited_once()
    snap = production_run_repo.add_item.await_args.kwargs
    assert snap["supply_name"] == "Harina de Trigo"
    assert snap["unit"] == "KG"
    assert snap["quantity_consumed"] == Decimal("5.00")


@pytest.mark.asyncio
async def test_get_preparation_missing_run_raises_not_found(mock_redis):
    """La preparación de una corrida inexistente lanza ProductionRunNotFoundError (404)."""
    from app.domain.exceptions import ProductionRunNotFoundError

    production_run_repo = AsyncMock()
    production_run_repo.get_context = AsyncMock(return_value=None)

    service = ProductionService(
        recipe_repo=AsyncMock(),
        supply_repo=AsyncMock(),
        batch_repo=AsyncMock(),
        movement_repo=AsyncMock(),
        production_run_repo=production_run_repo,
        category_repo=AsyncMock(),
        location_repo=AsyncMock(),
        alert_service=AlertService(redis=mock_redis),
        redis=mock_redis,
    )

    with pytest.raises(ProductionRunNotFoundError) as exc:
        await service.get_preparation(uuid.uuid4())
    assert exc.value.error_code == "PRODUCTION_RUN_NOT_FOUND"
