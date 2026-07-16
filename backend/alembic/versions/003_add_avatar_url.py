"""003 add avatar_url to users

Revision ID: 003
Revises: 002
Create Date: 2026-07-08

Añade el campo avatar_url a la tabla users para almacenar la ruta de la imagen
de perfil del usuario.
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("avatar_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "avatar_url")
