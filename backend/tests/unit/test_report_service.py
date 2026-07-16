"""HU-12: exportación CSV desnormalizada (OLAP-ready)."""
import csv
import io
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.services.report_service import CSV_COLUMNS, ReportService
from app.domain.enums import MovementType, UserRole


@pytest.mark.asyncio
async def test_export_csv_has_exact_olap_columns_and_adjustment_flag():
    row = {
        "movement_id": uuid.uuid4(),
        "timestamp": datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
        "user_id": uuid.uuid4(),
        "user_role": UserRole.ADMIN,
        "user_email": "admin@x.com",
        "supply_id": uuid.uuid4(),
        "supply_name": "Mantequilla",
        "item_type": "INGREDIENT",
        "category_name": "Lácteos",
        "location_code": "REF-01",
        "movement_type": MovementType.ADJUSTMENT_SUB,
        "quantity": Decimal("1.500"),
        "unit_cost": Decimal("4.0000"),
        "stock_before": Decimal("15.000"),
        "stock_after": Decimal("13.500"),
        "notes": "Error de digitación",
    }
    movement_repo = AsyncMock()
    movement_repo.export_denormalized = AsyncMock(return_value=[row])

    service = ReportService(movement_repo=movement_repo)
    content = await service.export_csv(start_date=None)

    # La exportación antepone un BOM UTF-8 (excel_compatible) que se ignora al parsear.
    reader = csv.DictReader(io.StringIO(content.removeprefix("﻿")))
    assert reader.fieldnames == CSV_COLUMNS
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["movement_type"] == "ADJUSTMENT_SUB"
    assert rows[0]["is_adjustment"] == "true"
    assert rows[0]["adjustment_reason"] == "Error de digitación"
    assert rows[0]["user_role"] == "ADMIN"
    assert rows[0]["location_code"] == "REF-01"
    assert rows[0]["item_type"] == "INGREDIENT"
    assert rows[0]["unit_cost"] == "4.0000"
    assert rows[0]["total_cost"] == "6.0000"   # 1.500 × 4.0000
