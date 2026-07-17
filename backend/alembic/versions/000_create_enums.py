"""000 create domain enums

Revision ID: 000
Revises:
Create Date: 2026-07-16

Los ENUMs vivían solo en sql/init.sql, que PostgreSQL ejecuta al primer arranque
cuando docker-compose lo monta en /docker-entrypoint-initdb.d. En un Postgres
gestionado (Railway) ese script nunca corre y la 001 falla al referenciar tipos
inexistentes. Crearlos aquí hace que el esquema dependa solo de Alembic.

Los bloques son idempotentes: en bases donde init.sql ya los creó, no hacen nada.
"""
from alembic import op

revision = "000"
down_revision = None
branch_labels = None
depends_on = None


ENUMS: dict[str, tuple[str, ...]] = {
    "user_role": ("SUPERADMIN", "ADMIN", "STAFF"),
    "unit_measure": ("KG", "GR", "L", "ML", "UNIT", "PKG", "BOX", "DOZEN"),
    "movement_type": (
        "ENTRY",
        "EXIT",
        "ADJUSTMENT_ADD",
        "ADJUSTMENT_SUB",
        "WASTE",
        "TRANSFER",
    ),
    "location_type": (
        "SHELF",
        "REFRIGERATOR",
        "FREEZER",
        "CABINET",
        "COUNTER",
        "WAREHOUSE",
    ),
}


def upgrade() -> None:
    for name, values in ENUMS.items():
        labels = ", ".join(f"'{v}'" for v in values)
        op.execute(
            f"""
            DO $$ BEGIN
                CREATE TYPE {name} AS ENUM ({labels});
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END $$;
            """
        )

    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')


def downgrade() -> None:
    for name in reversed(list(ENUMS)):
        op.execute(f"DROP TYPE IF EXISTS {name};")
