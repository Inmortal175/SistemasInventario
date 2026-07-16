"""002 batches, recipes, costs and traceability

Revision ID: 002
Revises: 001
Create Date: 2026-07-08

Añade el soporte para lotes FIFO (HU-13), valorización financiera (HU-16),
recetas/producción BOM (HU-15) y trazabilidad de ubicaciones (HU-10-03):

- supply_batches
- recipes / recipe_items
- locations.created_by
- movement_history.unit_cost
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Trazabilidad y costo en tablas existentes ────────────────────────────
    op.add_column(
        "locations",
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True,
        ),
    )
    op.add_column(
        "movement_history",
        sa.Column("unit_cost", sa.Numeric(12, 4), nullable=True),
    )

    # ── supply_batches (HU-13 / HU-16) ───────────────────────────────────────
    op.create_table(
        "supply_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "supply_item_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supply_items.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column("batch_code", sa.String(100), nullable=False),
        sa.Column("initial_stock", sa.Numeric(10, 3), nullable=False),
        sa.Column("current_stock", sa.Numeric(10, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("vendor_name", sa.String(255), nullable=True),
        sa.Column("expiration_date", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("alert_sent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("current_stock >= 0", name="chk_batch_stock_non_negative"),
        sa.CheckConstraint("unit_cost >= 0", name="chk_batch_cost_non_negative"),
    )
    op.create_index("ix_batch_supply", "supply_batches", ["supply_item_id"])
    op.create_index("ix_batch_code", "supply_batches", ["batch_code"])
    # Índice para el consumo FIFO: por insumo, activos, ordenados por vencimiento
    op.create_index(
        "ix_batch_fifo", "supply_batches",
        ["supply_item_id", "is_active", "expiration_date"],
    )

    # ── recipes (HU-15) ──────────────────────────────────────────────────────
    op.create_table(
        "recipes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "yield_unit",
            postgresql.ENUM("KG","GR","L","ML","UNIT","PKG","BOX","DOZEN",
                    name="unit_measure", create_type=False),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_recipes_name", "recipes", ["name"], unique=True)

    # ── recipe_items ─────────────────────────────────────────────────────────
    op.create_table(
        "recipe_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "recipe_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "supply_item_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supply_items.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column("quantity_per_unit", sa.Numeric(10, 3), nullable=False),
        sa.UniqueConstraint("recipe_id", "supply_item_id", name="uq_recipe_supply"),
        sa.CheckConstraint("quantity_per_unit > 0", name="chk_recipe_qty_positive"),
    )
    op.create_index("ix_recipe_items_recipe", "recipe_items", ["recipe_id"])


def downgrade() -> None:
    op.drop_table("recipe_items")
    op.drop_table("recipes")
    op.drop_table("supply_batches")
    op.drop_column("movement_history", "unit_cost")
    op.drop_column("locations", "created_by")
