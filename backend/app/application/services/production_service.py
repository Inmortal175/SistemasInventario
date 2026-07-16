import logging
import uuid
from datetime import date, timedelta
from decimal import Decimal

from redis.asyncio import Redis

from app.application.schemas.recipe_schema import (
    BatchPickPlan,
    PreparationBatch,
    PreparationIngredient,
    ProducedIngredient,
    ProductionHistoryResponse,
    ProductionPreparationResponse,
    ProductionResponse,
    ProductionRunResponse,
    ProductionSimulationResponse,
    RecipeCreate,
    RecipeListResponse,
    RecipeResponse,
    SimulatedIngredient,
)
from app.application.services.alert_service import AlertService
from app.domain.enums import ItemType, MovementType, UnitMeasure
from app.domain.exceptions import (
    ItemNotFoundError,
    ProductionRunNotFoundError,
    RecipeNotFoundError,
    RecipeProductionShortageError,
)
from app.infrastructure.cache.cache_keys import SUPPLIES_PAGE_PATTERN, stock_lock_key
from app.infrastructure.cache.redis_client import acquire_lock
from app.infrastructure.repositories.batch_repository import BatchRepository
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.infrastructure.repositories.location_repository import LocationRepository
from app.infrastructure.repositories.movement_repository import MovementRepository
from app.infrastructure.repositories.production_run_repository import (
    ProductionRunRepository,
)
from app.infrastructure.repositories.recipe_repository import RecipeRepository
from app.infrastructure.repositories.supply_repository import SupplyRepository

# Categoría bajo la que se agrupan los productos terminados auto-creados (HU-17).
_FINISHED_PRODUCTS_CATEGORY = "Productos terminados"

logger = logging.getLogger(__name__)


class ProductionService:
    """HU-15/HU-17: producción BOM con FIFO atómico y registro de lo producido."""

    def __init__(
        self,
        recipe_repo: RecipeRepository,
        supply_repo: SupplyRepository,
        batch_repo: BatchRepository,
        movement_repo: MovementRepository,
        production_run_repo: ProductionRunRepository,
        category_repo: CategoryRepository,
        location_repo: LocationRepository,
        alert_service: AlertService,
        redis: Redis,
    ) -> None:
        self._recipes = recipe_repo
        self._supplies = supply_repo
        self._batches = batch_repo
        self._movements = movement_repo
        self._runs = production_run_repo
        self._categories = category_repo
        self._locations = location_repo
        self._alert = alert_service
        self._redis = redis

    async def create_recipe(
        self, data: RecipeCreate, created_by_id: uuid.UUID
    ) -> RecipeResponse:
        # HU-17: si la receta define un producto, se crea el producto terminado
        # automáticamente (no se registra como insumo aparte) y se enlaza.
        produces_id: uuid.UUID | None = None
        if data.product_name and data.product_location_id:
            product = await self._create_finished_product_item(
                name=data.product_name,
                location_id=data.product_location_id,
                perishable=data.shelf_life_days is not None,
                created_by_id=created_by_id,
            )
            produces_id = product.id

        recipe = await self._recipes.create(
            name=data.name,
            description=data.description,
            yield_unit=data.yield_unit,
            produces_supply_item_id=produces_id,
            shelf_life_days=data.shelf_life_days,
            created_by=created_by_id,
        )
        for item in data.items:
            await self._recipes.add_item(
                recipe_id=recipe.id,
                supply_item_id=item.supply_item_id,
                quantity_per_unit=item.quantity_per_unit,
            )
        full = await self._recipes.get_with_items(recipe.id)
        return RecipeResponse.model_validate(full)

    async def _create_finished_product_item(
        self,
        name: str,
        location_id: uuid.UUID,
        perishable: bool,
        created_by_id: uuid.UUID,
    ) -> object:
        """Crea (o reutiliza la categoría de) un producto terminado como supply_item."""
        category = await self._categories.get_by_name(_FINISHED_PRODUCTS_CATEGORY)
        if category is None:
            category = await self._categories.create(
                name=_FINISHED_PRODUCTS_CATEGORY,
                slug="productos-terminados",
                description="Productos elaborados por receta (HU-17).",
                color_hex="#F59E0B",
                icon_name="cake",
                created_by=created_by_id,
            )
        return await self._supplies.create(
            name=name,
            sku=f"PT-{uuid.uuid4().hex[:8].upper()}",
            description=None,
            item_type=ItemType.FINISHED_PRODUCT,
            category_id=category.id,
            location_id=location_id,
            unit_of_measure=UnitMeasure.UNIT,
            current_stock=0,
            minimum_stock=0,
            maximum_stock=100000,
            unit_cost=0,
            is_perishable=perishable,
            expiration_date=None,
            supplier_name=None,
            created_by=created_by_id,
        )

    async def list_recipes(self) -> RecipeListResponse:
        recipes = await self._recipes.list_active()
        items = [RecipeResponse.model_validate(r) for r in recipes]
        return RecipeListResponse(items=items, total=len(items))

    async def simulate(
        self,
        recipe_id: uuid.UUID,
        quantity: int,
    ) -> ProductionSimulationResponse:
        """Simulacro de stock (dry-run) de HU-15: NO modifica nada.

        Permite al maestro pastelero preguntar "¿me alcanza para N unidades?" antes
        de comprometer la producción. Es de solo lectura: no adquiere locks ni
        escribe movimientos. Devuelve el desglose por ingrediente y la lista de los
        que faltan (con déficit), replicando la misma aritmética que `produce`.
        """
        recipe = await self._recipes.get_with_items(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(str(recipe_id))

        ingredients: list[SimulatedIngredient] = []
        for ri in recipe.items:
            item = await self._supplies.get_by_id(ri.supply_item_id)
            if item is None:
                raise ItemNotFoundError(str(ri.supply_item_id))
            required = ri.quantity_per_unit * quantity
            available = item.current_stock
            sufficient = available >= required

            # Lista de preparación: dónde está y de qué lotes sacarlo (FIFO, sin descontar).
            location = await self._locations.get_by_id(item.location_id)
            batch_plan = await self._build_pick_plan(item.id, required)

            ingredients.append(SimulatedIngredient(
                supply_id=item.id,
                supply_name=item.name,
                required=required,
                available=available,
                sufficient=sufficient,
                deficit=(required - available) if not sufficient else Decimal("0"),
                unit=item.unit_of_measure,
                location_code=location.code if location else None,
                location_type=location.location_type if location else None,
                batch_plan=batch_plan,
            ))

        missing = [i for i in ingredients if not i.sufficient]
        return ProductionSimulationResponse(
            recipe_id=recipe_id,
            recipe_name=recipe.name,
            quantity=quantity,
            feasible=len(missing) == 0,
            ingredients=ingredients,
            missing=missing,
        )

    async def produce(
        self,
        recipe_id: uuid.UUID,
        quantity: int,
        performed_by_id: uuid.UUID,
    ) -> ProductionResponse:
        """Produce `quantity` unidades descontando insumos por FIFO en una transacción.

        Fase 1 (validación): verifica que TODOS los ingredientes tengan stock
        suficiente. Si uno falla, lanza RecipeProductionShortageError y el
        dependency de sesión hace ROLLBACK — no se descuenta ningún insumo
        (HU-15-02).
        Fase 2 (descuento): consume FIFO cada ingrediente y registra un
        movimiento EXIT por ingrediente.
        """
        recipe = await self._recipes.get_with_items(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(str(recipe_id))

        # Un solo lock por producción evita deadlocks entre ingredientes.
        lock_key = f"lock:production:{recipe_id}"
        async with acquire_lock(self._redis, lock_key, timeout_seconds=10):
            needs: list[tuple[object, Decimal]] = []

            # ── Fase 1: validación total (antes de tocar el stock) ───────────
            for ri in recipe.items:
                item = await self._supplies.get_by_id_for_update(ri.supply_item_id)
                if item is None:
                    raise ItemNotFoundError(str(ri.supply_item_id))
                need = ri.quantity_per_unit * quantity
                if item.current_stock < need:
                    raise RecipeProductionShortageError(
                        supply_id=str(ri.supply_item_id),
                        required=need,
                        available=item.current_stock,
                    )
                needs.append((item, need))

            # ── Fase 2: descuento FIFO + movimientos ─────────────────────────
            produced: list[ProducedIngredient] = []
            alerts: list[tuple[uuid.UUID, str, Decimal, Decimal]] = []
            run_items: list[dict] = []   # snapshot de preparación (se asienta en Fase 4)
            total_ingredient_cost = Decimal("0")
            for item, need in needs:
                movement_id, cost, breakdown = await self._consume_ingredient(
                    item, need, performed_by_id, recipe.name
                )
                total_ingredient_cost += cost
                new_total = await self._batches.sum_active_stock(item.id)
                # Si el insumo no usa lotes, el stock ya fue actualizado abajo.
                if new_total == 0 and not await self._has_batches(item.id):
                    new_total = item.current_stock - need
                if new_total < item.minimum_stock:
                    alerts.append((item.id, item.name, new_total, item.minimum_stock))
                produced.append(ProducedIngredient(
                    supply_id=item.id,
                    supply_name=item.name,
                    consumed=need,
                    movement_id=movement_id,
                ))
                # Snapshot: dónde estaba y de qué lotes salió (para el historial).
                location = await self._locations.get_by_id(item.location_id)
                run_items.append({
                    "supply_item_id": item.id,
                    "supply_name": item.name,
                    "unit": item.unit_of_measure.value,
                    "location_code": location.code if location else None,
                    "quantity_consumed": need,
                    "unit_cost": (cost / need) if need else Decimal("0"),
                    "batch_breakdown": breakdown or None,
                })

            # ── Fase 3: ENTRY del producto terminado (HU-17) ─────────────────
            product_id, product_name, product_new_stock, product_batch_id = (
                await self._register_finished_product(
                    recipe, quantity, total_ingredient_cost, performed_by_id
                )
            )

            # ── Fase 4: asentar la corrida de producción (inmutable) ─────────
            run = await self._runs.create(
                recipe_id=recipe.id,
                product_supply_item_id=product_id,
                product_batch_id=product_batch_id,
                quantity_produced=Decimal(quantity),
                total_ingredient_cost=total_ingredient_cost,
                performed_by=performed_by_id,
            )
            # Snapshot de la lista de preparación usada (HU-17: "¿cómo se hizo?").
            for data in run_items:
                await self._runs.add_item(production_run_id=run.id, **data)

        await self._invalidate_supplies_cache()
        for supply_id, name, current, minimum in alerts:
            await self._alert.publish_low_stock(
                supply_item_id=supply_id,
                supply_name=name,
                current_stock=current,
                minimum_stock=minimum,
            )

        logger.info(
            "PRODUCTION_OK run=%s recipe=%s qty=%s ingredients=%s product=%s cost=%s",
            run.id, recipe_id, quantity, len(produced), product_id, total_ingredient_cost,
        )
        return ProductionResponse(
            recipe_id=recipe_id,
            recipe_name=recipe.name,
            quantity_produced=quantity,
            ingredients=produced,
            production_id=run.id,
            product_supply_item_id=product_id,
            product_name=product_name,
            product_new_stock=product_new_stock,
            total_ingredient_cost=total_ingredient_cost,
        )

    async def _register_finished_product(
        self,
        recipe: object,
        quantity: int,
        total_ingredient_cost: Decimal,
        performed_by_id: uuid.UUID,
    ) -> tuple[uuid.UUID | None, str | None, Decimal | None, uuid.UUID | None]:
        """Suma `quantity` al stock del producto terminado que genera la receta.

        Crea un lote (con vencimiento = hoy + vida útil) y un movimiento ENTRY, para
        que el producto se pueda vender luego por FIFO (HU-17). Si la receta no define
        producto que genera, no hace nada y la corrida se registra sin producto.
        Devuelve (product_id, product_name, nuevo_stock, batch_id).
        """
        product_id = getattr(recipe, "produces_supply_item_id", None)
        if product_id is None:
            return None, None, None, None

        product = await self._supplies.get_by_id_for_update(product_id)
        if product is None:
            raise ItemNotFoundError(str(product_id))

        qty = Decimal(quantity)
        stock_before = product.current_stock
        unit_cost = (total_ingredient_cost / qty) if qty else Decimal("0")

        expiration = None
        if recipe.shelf_life_days is not None:
            expiration = date.today() + timedelta(days=recipe.shelf_life_days)

        batch_code = f"PROD-{date.today():%Y%m%d}-{uuid.uuid4().hex[:5].upper()}"
        batch = await self._batches.create(
            supply_item_id=product.id,
            batch_code=batch_code,
            initial_stock=qty,
            current_stock=qty,
            unit_cost=unit_cost,
            vendor_name=None,
            expiration_date=expiration,
            is_active=True,
        )
        new_total = await self._batches.sum_active_stock(product.id)
        await self._supplies.update_stock(product.id, new_total)

        await self._movements.create(
            supply_item_id=product.id,
            movement_type=MovementType.ENTRY,
            quantity=qty,
            stock_before=stock_before,
            stock_after=new_total,
            notes=f"Producción de {quantity} × '{recipe.name}' (lote {batch_code})",
            unit_cost=unit_cost,
            alert_triggered=False,
            performed_by=performed_by_id,
        )
        return product.id, product.name, new_total, batch.id

    async def list_production_history(
        self, page: int = 1, limit: int = 20
    ) -> ProductionHistoryResponse:
        """HU-17-02: historial de corridas de producción, desc por fecha."""
        offset = (page - 1) * limit
        rows = await self._runs.list_with_context(limit=limit, offset=offset)
        total = await self._runs.count()
        items = [ProductionRunResponse(**row) for row in rows]
        return ProductionHistoryResponse(items=items, total=total, page=page, limit=limit)

    async def _build_pick_plan(
        self, supply_id: uuid.UUID, required: Decimal
    ) -> list[BatchPickPlan]:
        """Previsualiza el consumo FIFO de `required`: de qué lotes y cuánto de cada uno.

        Solo lectura (no bloquea ni descuenta). Replica el recorrido de
        `_consume_ingredient`. Si el insumo no maneja lotes, devuelve lista vacía
        y el insumo se ubica solo por su código de ubicación física.
        """
        batches = await self._batches.list_active_fifo(supply_id)
        plan: list[BatchPickPlan] = []
        remaining = required
        for batch in batches:
            if remaining <= 0:
                break
            take = min(batch.current_stock, remaining)
            plan.append(BatchPickPlan(
                batch_code=batch.batch_code,
                expiration_date=batch.expiration_date,
                take=take,
            ))
            remaining -= take
        return plan

    async def get_preparation(
        self, production_id: uuid.UUID
    ) -> ProductionPreparationResponse:
        """HU-17: reconstruye la lista de preparación de una corrida ya producida.

        Devuelve, para cada insumo consumido, cuánto, en qué unidad, de qué
        ubicación y de qué lotes salió (snapshot inmutable, no lectura en vivo).
        """
        context = await self._runs.get_context(production_id)
        if context is None:
            raise ProductionRunNotFoundError(str(production_id))

        rows = await self._runs.list_items(production_id)
        ingredients = [
            PreparationIngredient(
                supply_item_id=row.supply_item_id,
                supply_name=row.supply_name,
                unit=row.unit,
                location_code=row.location_code,
                quantity_consumed=row.quantity_consumed,
                unit_cost=row.unit_cost,
                batches=[
                    PreparationBatch(
                        batch_code=b["batch_code"],
                        expiration_date=b.get("expiration_date"),
                        quantity=b["quantity"],
                    )
                    for b in (row.batch_breakdown or [])
                ],
            )
            for row in rows
        ]
        return ProductionPreparationResponse(
            production_id=context["production_id"],
            recipe_name=context["recipe_name"],
            product_name=context["product_name"],
            quantity_produced=context["quantity_produced"],
            total_ingredient_cost=context["total_ingredient_cost"],
            performed_by_email=context["performed_by_email"],
            created_at=context["created_at"],
            ingredients=ingredients,
        )

    async def _has_batches(self, supply_id: uuid.UUID) -> bool:
        batches = await self._batches.list_active_by_supply(supply_id)
        return len(batches) > 0

    async def _consume_ingredient(
        self, item: object, need: Decimal, performed_by_id: uuid.UUID, recipe_name: str
    ) -> tuple[uuid.UUID, Decimal, list[dict]]:
        """Descuenta `need` del insumo (FIFO si tiene lotes; directo si no) y
        registra un movimiento EXIT.

        Devuelve (movement_id, costo_consumido, desglose_de_lotes), donde el
        desglose es una lista [{batch_code, expiration_date, quantity}] con los
        lotes efectivamente consumidos (vacía si el insumo no maneja lotes).
        """
        stock_before = item.current_stock
        batches = await self._batches.list_active_fifo_for_update(item.id)

        breakdown: list[dict] = []
        if batches:
            remaining = need
            weighted_cost = Decimal("0")
            desglose = []
            for batch in batches:
                if remaining <= 0:
                    break
                take = min(batch.current_stock, remaining)
                new_stock = batch.current_stock - take
                await self._batches.apply_consumption(batch.id, new_stock)
                weighted_cost += take * batch.unit_cost
                remaining -= take
                desglose.append(f"{batch.batch_code}:-{take}")
                breakdown.append({
                    "batch_code": batch.batch_code,
                    "expiration_date": (
                        batch.expiration_date.isoformat()
                        if batch.expiration_date else None
                    ),
                    "quantity": str(take),
                })
            new_total = await self._batches.sum_active_stock(item.id)
            consumed_cost = weighted_cost
            unit_cost = (weighted_cost / need) if need else Decimal("0")
            notes = f"Producción '{recipe_name}' FIFO [{'; '.join(desglose)}]"
        else:
            new_total = stock_before - need
            unit_cost = item.unit_cost
            consumed_cost = need * item.unit_cost
            notes = f"Producción '{recipe_name}'"

        await self._supplies.update_stock(item.id, new_total)
        movement = await self._movements.create(
            supply_item_id=item.id,
            movement_type=MovementType.EXIT,
            quantity=need,
            stock_before=stock_before,
            stock_after=new_total,
            notes=notes,
            unit_cost=unit_cost,
            alert_triggered=new_total < item.minimum_stock,
            performed_by=performed_by_id,
        )
        return movement.id, consumed_cost, breakdown

    async def _invalidate_supplies_cache(self) -> None:
        try:
            keys = [k async for k in self._redis.scan_iter(match=SUPPLIES_PAGE_PATTERN)]
            if keys:
                await self._redis.delete(*keys)
        except Exception as exc:  # noqa: BLE001
            logger.warning("REDIS_UNAVAILABLE invalidate_supplies err=%s", exc)
