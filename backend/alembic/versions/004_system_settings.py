"""004 system settings (nombre, logo y tema)

Revision ID: 004
Revises: 003
Create Date: 2026-07-08

Crea la tabla `system_settings` de fila única con la identidad visual de la
instalación e inserta la configuración por defecto.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "app_name",
            sa.String(80),
            nullable=False,
            server_default="PastryStock Manager",
        ),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("theme", sa.String(30), nullable=False, server_default="rosa"),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="chk_settings_singleton"),
    )

    op.execute(
        "INSERT INTO system_settings (id, app_name, theme) "
        "VALUES (1, 'PastryStock Manager', 'rosa')"
    )


def downgrade() -> None:
    op.drop_table("system_settings")
