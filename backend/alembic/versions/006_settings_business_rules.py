"""006 reglas de negocio e identidad fiscal en system_settings

Revision ID: 006
Revises: 005
Create Date: 2026-07-09

Mueve `expiration_alert_days` de variable de entorno a la base (es una decisión
del negocio, no del despliegue) y añade moneda, locale, tamaño de página,
opacidad del velo del login e identidad fiscal de la pastelería.
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

_NAMES = (
    "login_overlay_opacity",
    "expiration_alert_days",
    "currency_code",
    "locale",
    "page_size",
    "business_name",
    "tax_id",
    "address",
    "phone",
)

_CHECKS = (
    ("chk_settings_overlay", "login_overlay_opacity BETWEEN 0 AND 80"),
    ("chk_settings_expiration_days", "expiration_alert_days BETWEEN 1 AND 90"),
    ("chk_settings_page_size", "page_size BETWEEN 5 AND 100"),
)


def _columns() -> tuple[sa.Column, ...]:
    """Se construyen en cada llamada: un objeto Column solo puede asociarse a
    una tabla, y reutilizarlo entre upgrade y downgrade rompe en el mismo proceso."""
    return (
        sa.Column("login_overlay_opacity", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("expiration_alert_days", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="PEN"),
        sa.Column("locale", sa.String(10), nullable=False, server_default="es-PE"),
        sa.Column("page_size", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("business_name", sa.String(150), nullable=True),
        sa.Column("tax_id", sa.String(20), nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
    )


def upgrade() -> None:
    for column in _columns():
        op.add_column("system_settings", column)
    for name, condition in _CHECKS:
        op.create_check_constraint(name, "system_settings", condition)


def downgrade() -> None:
    for name, _ in _CHECKS:
        op.drop_constraint(name, "system_settings", type_="check")
    for name in _NAMES:
        op.drop_column("system_settings", name)
