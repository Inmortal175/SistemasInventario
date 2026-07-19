"""Datos de simulación: producción de Torta de Chocolate.

Crea un escenario completo y coherente para demos y pruebas manuales:
categorías, ubicaciones rotuladas, insumos con lotes perecederos, la receta
"Torta de Chocolate" y un historial de movimientos (ENTRY, EXIT por producción
y una WASTE).

Es idempotente: se apoya en los SKU/códigos con prefijo DEMO y no duplica nada
si se corre dos veces. No borra: `movement_history` es inmutable por diseño.

Uso:
    docker-compose exec backend python scripts/seed_demo.py
    docker-compose exec backend python scripts/seed_demo.py --cakes 5
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.domain.enums import ItemType, LocationType, MovementType, UnitMeasure  # noqa: E402
from app.infrastructure.cache.redis_client import close_redis, get_redis  # noqa: E402
from app.infrastructure.database.connection import AsyncSessionLocal, engine  # noqa: E402
from app.infrastructure.database.models.batch_model import SupplyBatchModel  # noqa: E402
from app.infrastructure.database.models.category_model import CategoryModel  # noqa: E402
from app.infrastructure.database.models.location_model import LocationModel  # noqa: E402
from app.infrastructure.database.models.movement_model import MovementHistoryModel  # noqa: E402
from app.infrastructure.database.models.production_model import (  # noqa: E402
    ProductionRunItemModel,
    ProductionRunModel,
)
from app.infrastructure.database.models.recipe_model import RecipeItemModel, RecipeModel  # noqa: E402
from app.infrastructure.database.models.supply_model import SupplyItemModel  # noqa: E402
from app.infrastructure.database.models.user_model import UserModel  # noqa: E402

RECIPE_NAME = "Torta de Chocolate"
TODAY = date.today()


def _slug(name: str) -> str:
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return "-".join(plain.lower().split())


CATEGORIES = [
    ("Secos y Harinas", "#D9A066", "wheat", "Harinas, azúcares y polvos de larga duración"),
    ("Lácteos y Frescos", "#7EC8E3", "cheese", "Perecederos que requieren refrigeración"),
    ("Chocolatería", "#6B4226", "cake", "Cacao, coberturas y derivados"),
    ("Aditivos y Esencias", "#C9A0DC", "jar", "Leudantes, esencias y sal"),
]

LOCATIONS = [
    ("ALM-01", LocationType.WAREHOUSE, "Almacén principal de secos", 500),
    ("EST-01-F1", LocationType.SHELF, "Estante 01, fila 1 — harinas y azúcares", 120),
    ("EST-02", LocationType.SHELF, "Estante 02 — chocolatería", 80),
    ("REF-01", LocationType.REFRIGERATOR, "Refrigeradora de lácteos", 60),
    ("FRZ-01", LocationType.FREEZER, "Congeladora de mantequillas", 40),
    ("CAB-01", LocationType.CABINET, "Armario de esencias y aditivos", 30),
]

# (sku, nombre, categoría, ubicación, unidad, stock, mínimo, máximo, costo,
#  perecedero, proveedor)
SUPPLIES = [
    ("DEMO-HAR-001", "Harina de trigo sin preparar", "Secos y Harinas", "EST-01-F1",
     UnitMeasure.KG, "25.000", "8.000", "60.000", "4.2000", False, "Molinos Anita"),
    ("DEMO-AZU-002", "Azúcar rubia", "Secos y Harinas", "EST-01-F1",
     UnitMeasure.KG, "30.000", "10.000", "70.000", "4.5000", False, "Cartavio"),
    ("DEMO-CAC-003", "Cacao en polvo alcalinizado", "Chocolatería", "EST-02",
     UnitMeasure.KG, "6.000", "2.000", "15.000", "32.0000", False, "Machu Picchu Foods"),
    ("DEMO-COB-004", "Chocolate cobertura bitter 70%", "Chocolatería", "EST-02",
     UnitMeasure.KG, "12.000", "4.000", "25.000", "45.0000", True, "Cacao Perú SAC"),
    ("DEMO-HUE-005", "Huevos de gallina pardos", "Lácteos y Frescos", "REF-01",
     UnitMeasure.UNIT, "180.000", "60.000", "360.000", "0.6500", True, "Granja San Isidro"),
    ("DEMO-MAN-006", "Mantequilla sin sal", "Lácteos y Frescos", "FRZ-01",
     UnitMeasure.KG, "9.000", "3.000", "20.000", "28.0000", True, "Laive"),
    ("DEMO-LEC-007", "Leche entera fresca", "Lácteos y Frescos", "REF-01",
     UnitMeasure.L, "14.000", "5.000", "30.000", "4.8000", True, "Gloria"),
    ("DEMO-POL-008", "Polvo de hornear", "Aditivos y Esencias", "CAB-01",
     UnitMeasure.GR, "800.000", "250.000", "2000.000", "0.0600", False, "Fleischmann"),
    ("DEMO-VAI-009", "Esencia de vainilla", "Aditivos y Esencias", "CAB-01",
     UnitMeasure.ML, "500.000", "150.000", "1000.000", "0.1200", False, "Negrita"),
    ("DEMO-SAL-010", "Sal fina", "Aditivos y Esencias", "CAB-01",
     UnitMeasure.GR, "1500.000", "300.000", "3000.000", "0.0020", False, "Emsal"),
]

# Lotes de los insumos perecederos. Uno vence en 5 días para que el cron de
# vencimientos (HU-13-03) tenga algo real que reportar en la demo.
# (sku, [(código, cantidad, costo, días_hasta_vencer)])
BATCHES = {
    "DEMO-COB-004": [
        ("LOTE-COB-2601", "5.000", "44.0000", 120),
        ("LOTE-COB-2602", "7.000", "45.5000", 210),
    ],
    "DEMO-HUE-005": [
        ("LOTE-HUE-2601", "60.000", "0.6200", 5),
        ("LOTE-HUE-2602", "120.000", "0.6600", 18),
    ],
    "DEMO-MAN-006": [
        ("LOTE-MAN-2601", "4.000", "27.5000", 45),
        ("LOTE-MAN-2602", "5.000", "28.4000", 90),
    ],
    "DEMO-LEC-007": [
        ("LOTE-LEC-2601", "6.000", "4.7000", 7),
        ("LOTE-LEC-2602", "8.000", "4.9000", 21),
    ],
}

# Bill of materials para UNA torta de chocolate de 8 porciones (molde 22 cm).
RECIPE_ITEMS = [
    ("DEMO-HAR-001", "0.250"),
    ("DEMO-AZU-002", "0.300"),
    ("DEMO-CAC-003", "0.075"),
    ("DEMO-COB-004", "0.200"),
    ("DEMO-HUE-005", "4.000"),
    ("DEMO-MAN-006", "0.180"),
    ("DEMO-LEC-007", "0.240"),
    ("DEMO-POL-008", "12.000"),
    ("DEMO-VAI-009", "10.000"),
    ("DEMO-SAL-010", "3.000"),
]

# Segunda receta: SÍ genera producto terminado (HU-17), así aparece en la sección
# de Productos con stock, lotes y vencimiento. Categoría propia "Productos terminados".
FINISHED_CATEGORY = "Productos terminados"
PRODUCT_RECIPE_NAME = "Brownie de Chocolate"
PRODUCT_NAME = "Brownie de Chocolate (bandeja x12)"
PRODUCT_SKU = "DEMO-PT-BROWNIE"
PRODUCT_LOCATION = "REF-01"   # se refrigera para vender luego
PRODUCT_SHELF_LIFE_DAYS = 5
PRODUCT_RUNS = 3              # corridas ya producidas (cada una suma una bandeja)

# BOM para UNA bandeja de brownies.
PRODUCT_RECIPE_ITEMS = [
    ("DEMO-HAR-001", "0.180"),
    ("DEMO-AZU-002", "0.220"),
    ("DEMO-CAC-003", "0.060"),
    ("DEMO-COB-004", "0.150"),
    ("DEMO-HUE-005", "3.000"),
    ("DEMO-MAN-006", "0.160"),
]


async def _resolve_actor(session) -> UserModel:
    """Usa el SUPERADMIN configurado; si no existe, el usuario activo más antiguo."""
    settings = get_settings()
    stmt = select(UserModel).where(UserModel.email == settings.superadmin_email.lower())
    actor = (await session.execute(stmt)).scalar_one_or_none()
    if actor is not None:
        return actor

    stmt = (
        select(UserModel)
        .where(UserModel.is_active == True)  # noqa: E712
        .order_by(UserModel.created_at)
        .limit(1)
    )
    actor = (await session.execute(stmt)).scalar_one_or_none()
    if actor is None:
        raise SystemExit(
            "✗ No hay usuarios en la base. Corre primero scripts/seed_admin.py"
        )
    return actor


async def _seed_categories(session, actor: UserModel) -> dict[str, CategoryModel]:
    out: dict[str, CategoryModel] = {}
    for name, color, icon, desc in CATEGORIES:
        stmt = select(CategoryModel).where(CategoryModel.slug == _slug(name))
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing is None:
            existing = CategoryModel(
                name=name,
                slug=_slug(name),
                description=desc,
                color_hex=color,
                icon_name=icon,
                created_by=actor.id,
            )
            session.add(existing)
            await session.flush()
        out[name] = existing
    return out


async def _seed_locations(session, actor: UserModel) -> dict[str, LocationModel]:
    out: dict[str, LocationModel] = {}
    for code, ltype, desc, cap in LOCATIONS:
        stmt = select(LocationModel).where(LocationModel.code == code)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing is None:
            existing = LocationModel(
                code=code,
                description=desc,
                location_type=ltype,
                capacity_units=cap,
                created_by=actor.id,
            )
            session.add(existing)
            await session.flush()
        out[code] = existing
    return out


async def _seed_supplies(
    session,
    actor: UserModel,
    categories: dict[str, CategoryModel],
    locations: dict[str, LocationModel],
) -> dict[str, SupplyItemModel]:
    out: dict[str, SupplyItemModel] = {}
    entry_at = datetime.now(timezone.utc) - timedelta(days=10)

    for (sku, name, cat, loc, unit, stock, minimum, maximum,
         cost, perishable, vendor) in SUPPLIES:
        stmt = select(SupplyItemModel).where(SupplyItemModel.sku == sku)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            out[sku] = existing
            continue

        batch_specs = BATCHES.get(sku, [])
        expiry = (
            min(TODAY + timedelta(days=d) for _, _, _, d in batch_specs)
            if batch_specs
            else None
        )

        item = SupplyItemModel(
            name=name,
            sku=sku,
            description=f"Insumo de demostración para la receta '{RECIPE_NAME}'.",
            category_id=categories[cat].id,
            location_id=locations[loc].id,
            unit_of_measure=unit,
            current_stock=Decimal(stock),
            minimum_stock=Decimal(minimum),
            maximum_stock=Decimal(maximum),
            unit_cost=Decimal(cost),
            is_perishable=perishable,
            expiration_date=expiry,
            supplier_name=vendor,
            created_by=actor.id,
        )
        session.add(item)
        await session.flush()

        for code, qty, batch_cost, days in batch_specs:
            session.add(SupplyBatchModel(
                supply_item_id=item.id,
                batch_code=code,
                initial_stock=Decimal(qty),
                current_stock=Decimal(qty),
                unit_cost=Decimal(batch_cost),
                vendor_name=vendor,
                expiration_date=TODAY + timedelta(days=days),
            ))

        session.add(MovementHistoryModel(
            supply_item_id=item.id,
            movement_type=MovementType.ENTRY,
            quantity=Decimal(stock),
            stock_before=Decimal("0"),
            stock_after=Decimal(stock),
            notes=f"Compra inicial a {vendor}",
            unit_cost=Decimal(cost),
            performed_by=actor.id,
            created_at=entry_at,
        ))
        out[sku] = item

    await session.flush()
    return out


async def _seed_recipe(
    session, actor: UserModel, supplies: dict[str, SupplyItemModel]
) -> RecipeModel:
    stmt = select(RecipeModel).where(RecipeModel.name == RECIPE_NAME)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing

    recipe = RecipeModel(
        name=RECIPE_NAME,
        description="Torta húmeda de chocolate, molde 22 cm, rinde 8 porciones.",
        yield_unit=UnitMeasure.UNIT,
        created_by=actor.id,
    )
    session.add(recipe)
    await session.flush()

    for sku, qty in RECIPE_ITEMS:
        session.add(RecipeItemModel(
            recipe_id=recipe.id,
            supply_item_id=supplies[sku].id,
            quantity_per_unit=Decimal(qty),
        ))
    await session.flush()
    return recipe


async def _seed_finished_category(session, actor: UserModel) -> CategoryModel:
    """Categoría 'Productos terminados' (misma que auto-crea ProductionService)."""
    stmt = select(CategoryModel).where(CategoryModel.slug == _slug(FINISHED_CATEGORY))
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is None:
        existing = CategoryModel(
            name=FINISHED_CATEGORY,
            slug=_slug(FINISHED_CATEGORY),
            description="Productos elaborados por receta (HU-17).",
            color_hex="#F59E0B",
            icon_name="cake",
            created_by=actor.id,
        )
        session.add(existing)
        await session.flush()
    return existing


async def _seed_product(
    session, actor: UserModel, category: CategoryModel, location: LocationModel
) -> SupplyItemModel:
    """Producto terminado (item_type=FINISHED_PRODUCT) que genera la 2ª receta."""
    stmt = select(SupplyItemModel).where(SupplyItemModel.sku == PRODUCT_SKU)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing
    product = SupplyItemModel(
        name=PRODUCT_NAME,
        sku=PRODUCT_SKU,
        description="Producto terminado de demostración (se produce por receta).",
        item_type=ItemType.FINISHED_PRODUCT,
        category_id=category.id,
        location_id=location.id,
        unit_of_measure=UnitMeasure.UNIT,
        current_stock=Decimal("0"),
        minimum_stock=Decimal("0"),
        maximum_stock=Decimal("100000"),
        unit_cost=Decimal("0"),
        is_perishable=True,
        expiration_date=None,
        supplier_name=None,
        created_by=actor.id,
    )
    session.add(product)
    await session.flush()
    return product


async def _seed_product_recipe(
    session, actor: UserModel, supplies: dict[str, SupplyItemModel], product: SupplyItemModel
) -> RecipeModel:
    stmt = select(RecipeModel).where(RecipeModel.name == PRODUCT_RECIPE_NAME)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing
    recipe = RecipeModel(
        name=PRODUCT_RECIPE_NAME,
        description="Bandeja de 12 brownies húmedos de chocolate.",
        yield_unit=UnitMeasure.UNIT,
        produces_supply_item_id=product.id,
        shelf_life_days=PRODUCT_SHELF_LIFE_DAYS,
        created_by=actor.id,
    )
    session.add(recipe)
    await session.flush()
    for sku, qty in PRODUCT_RECIPE_ITEMS:
        session.add(RecipeItemModel(
            recipe_id=recipe.id,
            supply_item_id=supplies[sku].id,
            quantity_per_unit=Decimal(qty),
        ))
    await session.flush()
    return recipe


async def _produce_product(
    session,
    actor: UserModel,
    supplies: dict[str, SupplyItemModel],
    locations: dict[str, LocationModel],
    product: SupplyItemModel,
    recipe: RecipeModel,
) -> int:
    """Produce PRODUCT_RUNS bandejas ya fabricadas: descuenta insumos por FIFO,
    suma stock al producto terminado (lote con vencimiento + ENTRY) y asienta cada
    corrida con su lista de preparación. Idempotente: si el producto ya tiene stock,
    no vuelve a producir.
    """
    if product.current_stock > 0:
        return 0

    code_by_location_id = {loc.id: code for code, loc in locations.items()}
    produced = 0
    for day in range(PRODUCT_RUNS):
        produced_at = datetime.now(timezone.utc) - timedelta(days=PRODUCT_RUNS - day, hours=6)
        run = ProductionRunModel(
            recipe_id=recipe.id,
            product_supply_item_id=product.id,
            product_batch_id=None,
            quantity_produced=Decimal("1"),
            total_ingredient_cost=Decimal("0"),
            performed_by=actor.id,
            created_at=produced_at,
        )
        session.add(run)
        await session.flush()

        run_cost = Decimal("0")
        for sku, qty in PRODUCT_RECIPE_ITEMS:
            item = supplies[sku]
            need = Decimal(qty)
            before, after, notes, breakdown, cost = await _consume_fifo(session, item, need)
            run_cost += cost
            session.add(MovementHistoryModel(
                supply_item_id=item.id,
                movement_type=MovementType.EXIT,
                quantity=need,
                stock_before=before,
                stock_after=after,
                notes=notes,
                unit_cost=item.unit_cost,
                alert_triggered=after < item.minimum_stock,
                performed_by=actor.id,
                created_at=produced_at,
            ))
            session.add(ProductionRunItemModel(
                production_run_id=run.id,
                supply_item_id=item.id,
                supply_name=item.name,
                unit=item.unit_of_measure.value,
                location_code=code_by_location_id.get(item.location_id),
                quantity_consumed=need,
                unit_cost=(cost / need) if need else Decimal("0"),
                batch_breakdown=breakdown or None,
                created_at=produced_at,
            ))

        # Suma una bandeja al producto terminado: lote con vencimiento + ENTRY.
        qty = Decimal("1")
        unit_cost = run_cost / qty
        batch_code = f"PROD-{produced_at.date():%Y%m%d}-{day + 1:02d}"
        product_batch = SupplyBatchModel(
            supply_item_id=product.id,
            batch_code=batch_code,
            initial_stock=qty,
            current_stock=qty,
            unit_cost=unit_cost,
            vendor_name=None,
            expiration_date=produced_at.date() + timedelta(days=PRODUCT_SHELF_LIFE_DAYS),
        )
        session.add(product_batch)
        await session.flush()

        stock_before = product.current_stock
        product.current_stock = stock_before + qty
        product.unit_cost = unit_cost
        run.product_batch_id = product_batch.id
        run.total_ingredient_cost = run_cost
        session.add(MovementHistoryModel(
            supply_item_id=product.id,
            movement_type=MovementType.ENTRY,
            quantity=qty,
            stock_before=stock_before,
            stock_after=product.current_stock,
            notes=f"Producción de 1 × '{recipe.name}' (lote {batch_code})",
            unit_cost=unit_cost,
            alert_triggered=False,
            performed_by=actor.id,
            created_at=produced_at,
        ))
        produced += 1
        await session.flush()
    return produced


async def _consume_fifo(
    session, item: SupplyItemModel, need: Decimal
) -> tuple[Decimal, Decimal, str, list[dict], Decimal]:
    """Descuenta `need` del insumo replicando el FIFO de ProductionService.

    Devuelve (stock_antes, stock_después, nota, desglose_de_lotes, costo_consumido).
    El desglose es [{batch_code, expiration_date, quantity}] (vacío si no hay lotes).
    Los lotes se agotan por fecha de vencimiento más próxima primero.
    """
    stock_before = item.current_stock
    stmt = (
        select(SupplyBatchModel)
        .where(
            SupplyBatchModel.supply_item_id == item.id,
            SupplyBatchModel.is_active == True,  # noqa: E712
            SupplyBatchModel.current_stock > 0,
        )
        .order_by(SupplyBatchModel.expiration_date)
    )
    batches = list((await session.execute(stmt)).scalars().all())

    if not batches:
        item.current_stock = stock_before - need
        cost = need * item.unit_cost
        return stock_before, item.current_stock, f"Producción '{RECIPE_NAME}'", [], cost

    remaining = need
    trace: list[str] = []
    breakdown: list[dict] = []
    consumed_cost = Decimal("0")
    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.current_stock, remaining)
        batch.current_stock -= take
        remaining -= take
        consumed_cost += take * batch.unit_cost
        trace.append(f"{batch.batch_code}:-{take}")
        breakdown.append({
            "batch_code": batch.batch_code,
            "expiration_date": (
                batch.expiration_date.isoformat() if batch.expiration_date else None
            ),
            "quantity": str(take),
        })

    item.current_stock = sum((b.current_stock for b in batches), Decimal("0"))
    note = f"Producción '{RECIPE_NAME}' FIFO [{'; '.join(trace)}]"
    return stock_before, item.current_stock, note, breakdown, consumed_cost


async def _seed_movements(
    session,
    actor: UserModel,
    supplies: dict[str, SupplyItemModel],
    locations: dict[str, LocationModel],
    recipe: RecipeModel,
    cakes: int,
) -> int:
    """Simula `cakes` tortas producidas en días distintos + una merma de huevos.

    Cada torta genera, además del EXIT por ingrediente, una corrida de producción
    (`production_runs`) con su lista de preparación (`production_run_items`): dónde
    salió cada insumo, cuánto y de qué lotes. Así el historial y el modal de
    preparación tienen datos reales en la demo.

    La merma de huevos es el último registro que escribe esta función, así que
    su presencia marca el bloque completo como ya sembrado: sin esa guarda, una
    segunda corrida volvería a descontar stock.
    """
    huevos = supplies["DEMO-HUE-005"]
    stmt = select(MovementHistoryModel).where(
        MovementHistoryModel.supply_item_id == huevos.id,
        MovementHistoryModel.movement_type == MovementType.WASTE,
    )
    if (await session.execute(stmt)).first() is not None:
        return 0

    code_by_location_id = {loc.id: code for code, loc in locations.items()}

    written = 0
    for day in range(cakes):
        produced_at = datetime.now(timezone.utc) - timedelta(days=cakes - day, hours=3)
        run = ProductionRunModel(
            recipe_id=recipe.id,
            product_supply_item_id=None,
            product_batch_id=None,
            quantity_produced=Decimal("1"),
            total_ingredient_cost=Decimal("0"),
            performed_by=actor.id,
            created_at=produced_at,
        )
        session.add(run)
        await session.flush()

        run_cost = Decimal("0")
        for sku, qty in RECIPE_ITEMS:
            item = supplies[sku]
            need = Decimal(qty)
            before, after, notes, breakdown, cost = await _consume_fifo(session, item, need)
            run_cost += cost
            session.add(MovementHistoryModel(
                supply_item_id=item.id,
                movement_type=MovementType.EXIT,
                quantity=need,
                stock_before=before,
                stock_after=after,
                notes=notes,
                unit_cost=item.unit_cost,
                alert_triggered=after < item.minimum_stock,
                performed_by=actor.id,
                created_at=produced_at,
            ))
            session.add(ProductionRunItemModel(
                production_run_id=run.id,
                supply_item_id=item.id,
                supply_name=item.name,
                unit=item.unit_of_measure.value,
                location_code=code_by_location_id.get(item.location_id),
                quantity_consumed=need,
                unit_cost=(cost / need) if need else Decimal("0"),
                batch_breakdown=breakdown or None,
                created_at=produced_at,
            ))
            written += 1
        run.total_ingredient_cost = run_cost
        await session.flush()

    merma = Decimal("6.000")
    before, after, _, _, _ = await _consume_fifo(session, huevos, merma)
    session.add(MovementHistoryModel(
        supply_item_id=huevos.id,
        movement_type=MovementType.WASTE,
        quantity=merma,
        stock_before=before,
        stock_after=after,
        notes="Merma: huevos trizados al descargar la jaba",
        unit_cost=huevos.unit_cost,
        alert_triggered=after < huevos.minimum_stock,
        performed_by=actor.id,
        created_at=datetime.now(timezone.utc) - timedelta(days=1),
    ))
    return written + 1


# Cachés cache-first que la app sirve sin tocar Postgres. El seed escribe directo
# a la DB, así que hay que invalidarlas o el frontend seguiría mostrando lo viejo
# (típicamente listas vacías cacheadas antes de sembrar).
_CACHE_PATTERNS = [
    "categories:*",
    "category:*",
    "supplies:page:*",
    "dashboard:kpis",
]


async def _invalidate_cache() -> int:
    redis = await get_redis()
    deleted = 0
    for pattern in _CACHE_PATTERNS:
        if "*" in pattern:
            keys = [key async for key in redis.scan_iter(match=pattern, count=500)]
            if keys:
                deleted += await redis.delete(*keys)
        else:
            deleted += await redis.delete(pattern)
    return deleted


async def seed(cakes: int) -> int:
    async with AsyncSessionLocal() as session:
        actor = await _resolve_actor(session)
        categories = await _seed_categories(session, actor)
        locations = await _seed_locations(session, actor)
        supplies = await _seed_supplies(session, actor, categories, locations)
        recipe = await _seed_recipe(session, actor, supplies)
        movements = await _seed_movements(
            session, actor, supplies, locations, recipe, cakes
        )
        # 2ª receta con producto terminado → aparece en la sección de Productos.
        finished_cat = await _seed_finished_category(session, actor)
        product = await _seed_product(
            session, actor, finished_cat, locations[PRODUCT_LOCATION]
        )
        product_recipe = await _seed_product_recipe(session, actor, supplies, product)
        product_units = await _produce_product(
            session, actor, supplies, locations, product, product_recipe
        )
        await session.commit()

    cache_deleted = await _invalidate_cache()

    print(
        f"✅ Datos de simulación listos (actor: {actor.email})\n"
        f"   categorías:  {len(categories) + 1}\n"
        f"   ubicaciones: {len(locations)}\n"
        f"   insumos:     {len(supplies)}\n"
        f"   recetas:     2 ({recipe.name} + {product_recipe.name} → produce terminado)\n"
        f"   productos:   {product.name} ({product_units} bandejas en stock)\n"
        f"   producción:  {cakes} tortas + {product_units} bandejas, con lista de preparación\n"
        f"   movimientos: {movements} nuevos (tortas + merma)\n"
        f"   caché:       {cache_deleted} llaves de Redis invalidadas"
    )
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description=f"Siembra el escenario '{RECIPE_NAME}'.")
    parser.add_argument(
        "--cakes",
        type=int,
        default=3,
        help="Tortas a simular como ya producidas (default: 3).",
    )
    args = parser.parse_args()
    if args.cakes < 0:
        raise SystemExit("✗ --cakes no puede ser negativo.")
    try:
        return await seed(args.cakes)
    finally:
        await close_redis()
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
