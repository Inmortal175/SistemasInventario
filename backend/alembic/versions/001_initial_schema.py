"""001 initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-07

Crea todas las tablas del MVP con sus constraints e índices de rendimiento.
Los ENUMs se crean previamente en sql/init.sql para que PostgreSQL los tenga
disponibles antes de que Alembic ejecute este script.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("SUPERADMIN", "ADMIN", "STAFF", name="user_role", create_type=False),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    # ── locations ────────────────────────────────────────────────────────────
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column(
            "location_type",
            postgresql.ENUM(
                "SHELF", "REFRIGERATOR", "FREEZER", "CABINET", "COUNTER", "WAREHOUSE",
                name="location_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("capacity_units", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            r"code ~ '^(EST|REF|FRZ|CAB|CON|ALM)-\d{2}(-F\d{1,2})?$'",
            name="chk_location_code_pattern",
        ),
    )
    op.create_index("ix_locations_code", "locations", ["code"], unique=True)

    # ── dynamic_categories ───────────────────────────────────────────────────
    op.create_table(
        "dynamic_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("color_hex", sa.String(7), nullable=False),
        sa.Column("icon_name", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_categories_name", "dynamic_categories", ["name"], unique=True)
    op.create_index("ix_categories_slug_active", "dynamic_categories", ["slug", "is_active"])

    # ── supply_items ─────────────────────────────────────────────────────────
    op.create_table(
        "supply_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "category_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dynamic_categories.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column(
            "location_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column(
            "unit_of_measure",
            postgresql.ENUM("KG","GR","L","ML","UNIT","PKG","BOX","DOZEN",
                    name="unit_measure", create_type=False),
            nullable=False,
        ),
        sa.Column("current_stock", sa.Numeric(10, 3), nullable=False, server_default="0"),
        sa.Column("minimum_stock", sa.Numeric(10, 3), nullable=False, server_default="0"),
        sa.Column("maximum_stock", sa.Numeric(10, 3), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("is_perishable", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("expiration_date", sa.Date, nullable=True),
        sa.Column("supplier_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("current_stock >= 0", name="chk_stock_non_negative"),
        sa.CheckConstraint("minimum_stock <= maximum_stock", name="chk_stock_range"),
        sa.CheckConstraint("unit_cost >= 0", name="chk_cost_non_negative"),
    )
    op.create_index("ix_supply_sku", "supply_items", ["sku"], unique=True)
    op.create_index("ix_supply_category_active", "supply_items", ["category_id", "is_active"])
    op.create_index("ix_supply_name", "supply_items", ["name"])

    # ── movement_history ─────────────────────────────────────────────────────
    op.create_table(
        "movement_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "supply_item_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supply_items.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column(
            "movement_type",
            postgresql.ENUM(
                "ENTRY","EXIT","ADJUSTMENT_ADD","ADJUSTMENT_SUB","WASTE","TRANSFER",
                name="movement_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("stock_before", sa.Numeric(10, 3), nullable=False),
        sa.Column("stock_after", sa.Numeric(10, 3), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("alert_triggered", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "performed_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
        ),
        # Sin updated_at — inmutabilidad de auditoría
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_movement_item_date", "movement_history",
                    ["supply_item_id", "created_at"])
    op.create_index("ix_movement_performer", "movement_history", ["performed_by"])


def downgrade() -> None:
    op.drop_table("movement_history")
    op.drop_table("supply_items")
    op.drop_table("dynamic_categories")
    op.drop_table("locations")
    op.drop_table("users")
