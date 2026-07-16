"""008 production run items (snapshot de preparación)

Revision ID: 008
Revises: 007
Create Date: 2026-07-15

Guarda, por cada corrida de producción, el desglose inmutable de qué insumo se
consumió, cuánto, en qué unidad, de qué ubicación y de qué lotes (FIFO). Es un
SNAPSHOT: nombre/unidad/ubicación/lotes se copian al producir para que el
historial siga siendo legible aunque luego cambien o se borren esos datos.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "production_run_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "production_run_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_runs.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column(
            "supply_item_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supply_items.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column("supply_name", sa.String(255), nullable=False),
        sa.Column("unit", sa.String(10), nullable=False),
        sa.Column("location_code", sa.String(20), nullable=True),
        sa.Column("quantity_consumed", sa.Numeric(10, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 4), nullable=False, server_default="0"),
        # Lista de lotes consumidos [{batch_code, expiration_date, quantity}], FIFO.
        sa.Column("batch_breakdown", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_prod_run_item_run", "production_run_items", ["production_run_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_prod_run_item_run", table_name="production_run_items")
    op.drop_table("production_run_items")
