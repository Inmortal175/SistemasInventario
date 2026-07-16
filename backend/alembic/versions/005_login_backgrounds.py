"""005 fondos del login por dispositivo

Revision ID: 005
Revises: 004
Create Date: 2026-07-09

Añade una imagen de fondo del login por familia de dispositivo (móvil, tablet,
escritorio). Las tres son opcionales.
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

_COLUMNS = (
    "login_bg_mobile_url",
    "login_bg_tablet_url",
    "login_bg_desktop_url",
)


def upgrade() -> None:
    for column in _COLUMNS:
        op.add_column("system_settings", sa.Column(column, sa.String(500), nullable=True))


def downgrade() -> None:
    for column in _COLUMNS:
        op.drop_column("system_settings", column)
