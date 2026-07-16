"""007 finished products and production runs

Revision ID: 007
Revises: 006
Create Date: 2026-07-10

HU-17: producto terminado como inventario y registro de producción.

- supply_items.item_type          → INGREDIENT (default) | FINISHED_PRODUCT
- recipes.produces_supply_item_id → producto terminado que genera la receta
- recipes.shelf_life_days         → vida útil del producto producido (vencimiento del lote)
- production_runs                 → asiento inmutable de cada corrida de producción
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── supply_items.item_type (texto + CHECK, sin ENUM nativo de PG) ────────
    op.add_column(
        "supply_items",
        sa.Column(
            "item_type",
            sa.String(20),
            nullable=False,
            server_default="INGREDIENT",
        ),
    )
    op.create_check_constraint(
        "chk_item_type_valid",
        "supply_items",
        "item_type IN ('INGREDIENT', 'FINISHED_PRODUCT')",
    )
    op.create_index("ix_supply_item_type", "supply_items", ["item_type"])

    # ── recipes: producto terminado que genera + vida útil ───────────────────
    op.add_column(
        "recipes",
        sa.Column(
            "produces_supply_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supply_items.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "recipes",
        sa.Column("shelf_life_days", sa.Integer, nullable=True),
    )

    # ── production_runs (HU-17) ──────────────────────────────────────────────
    op.create_table(
        "production_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "recipe_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recipes.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column(
            "product_supply_item_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supply_items.id", ondelete="RESTRICT"), nullable=True,
        ),
        sa.Column(
            "product_batch_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supply_batches.id", ondelete="RESTRICT"), nullable=True,
        ),
        sa.Column("quantity_produced", sa.Numeric(10, 3), nullable=False),
        sa.Column("total_ingredient_cost", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column(
            "performed_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("quantity_produced > 0", name="chk_production_qty_positive"),
    )
    op.create_index("ix_production_recipe", "production_runs", ["recipe_id"])
    op.create_index("ix_production_performer", "production_runs", ["performed_by"])
    op.create_index("ix_production_created", "production_runs", ["created_at"])


def downgrade() -> None:
    op.drop_table("production_runs")
    op.drop_column("recipes", "shelf_life_days")
    op.drop_column("recipes", "produces_supply_item_id")
    op.drop_index("ix_supply_item_type", table_name="supply_items")
    op.drop_constraint("chk_item_type_valid", "supply_items", type_="check")
    op.drop_column("supply_items", "item_type")
