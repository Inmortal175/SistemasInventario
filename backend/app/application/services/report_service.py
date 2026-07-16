import csv
import io
from datetime import date
from decimal import Decimal

from app.domain.enums import MovementType
from app.infrastructure.repositories.movement_repository import MovementRepository

# Columnas exactas exigidas por HU-12-01 (orden fijo para ingestión OLAP).
# item_type distingue consumo de insumo vs. producción de producto terminado;
# unit_cost/total_cost habilitan el análisis financiero; notes lleva el motivo.
CSV_COLUMNS = [
    "movement_id", "timestamp", "user_id", "user_role", "user_email",
    "supply_id", "supply_name", "item_type", "category_name", "location_code",
    "movement_type", "quantity", "unit_cost", "total_cost",
    "stock_before", "stock_after",
    "is_adjustment", "adjustment_reason", "notes",
]

_ADJUSTMENT_TYPES = {MovementType.ADJUSTMENT_ADD, MovementType.ADJUSTMENT_SUB}

# Excel en Windows asume la codificación ANSI local (Windows-1252 en español) si
# el archivo no empieza con esta marca: "Azúcar" se leería "AzÃºcar". PowerBI y
# pandas la ignoran (utf-8-sig), pero algunos ingestores estrictos la tratarían
# como parte de la primera columna — de ahí que sea opcional.
UTF8_BOM = "﻿"


class ReportService:
    """HU-12: exportación desnormalizada (OLAP-ready)."""

    def __init__(self, movement_repo: MovementRepository) -> None:
        self._movements = movement_repo

    async def count_rows(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> int:
        """Cuántos movimientos entraría en el CSV. Evita descargar a ciegas."""
        rows = await self._movements.export_denormalized(start_date, end_date)
        return len(rows)

    async def export_csv(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        excel_compatible: bool = True,
    ) -> str:
        rows = await self._movements.export_denormalized(start_date, end_date)

        buffer = io.StringIO()
        if excel_compatible:
            buffer.write(UTF8_BOM)
        writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()

        for row in rows:
            mtype = row["movement_type"]
            is_adjustment = mtype in _ADJUSTMENT_TYPES
            mtype_value = mtype.value if hasattr(mtype, "value") else str(mtype)
            role = row["user_role"]
            role_value = role.value if hasattr(role, "value") else str(role)
            item_type = row.get("item_type")
            item_type_value = (
                item_type.value if hasattr(item_type, "value") else (item_type or "")
            )
            quantity = row["quantity"]
            unit_cost = row.get("unit_cost")
            total_cost = (
                (quantity * unit_cost).quantize(Decimal("0.0001"))
                if unit_cost is not None else ""
            )
            writer.writerow({
                "movement_id": row["movement_id"],
                "timestamp": row["timestamp"].isoformat() if row["timestamp"] else "",
                "user_id": row["user_id"],
                "user_role": role_value,
                "user_email": row["user_email"],
                "supply_id": row["supply_id"],
                "supply_name": row["supply_name"],
                "item_type": item_type_value,
                "category_name": row["category_name"],
                "location_code": row["location_code"],
                "movement_type": mtype_value,
                "quantity": quantity,
                "unit_cost": unit_cost if unit_cost is not None else "",
                "total_cost": total_cost,
                "stock_before": row["stock_before"],
                "stock_after": row["stock_after"],
                "is_adjustment": str(is_adjustment).lower(),
                # La razón del ajuste se guarda en notes (columna reutilizada).
                "adjustment_reason": row["notes"] if is_adjustment else "",
                "notes": row.get("notes") or "",
            })

        return buffer.getvalue()
