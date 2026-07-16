from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.api.v1.providers import ReportServiceDep
from app.core.dependencies import require_roles
from app.domain.enums import UserRole
from app.infrastructure.database.models.user_model import UserModel

router = APIRouter(prefix="/reports", tags=["Reportes"])

# HU-12-02: los reportes globales son exclusivos de ADMIN+ (STAFF → 403).
_AdminOnly = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.SUPERADMIN))]

_StartDate = Annotated[date | None, Query(description="Inclusive, desde las 00:00 UTC.")]
_EndDate = Annotated[date | None, Query(description="Inclusive, hasta las 23:59 UTC.")]


def _validate_range(start_date: date | None, end_date: date | None) -> None:
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fecha final no puede ser anterior a la inicial.",
        )


@router.get("/export/count")
async def count_report_rows(
    service: ReportServiceDep,
    current_user: _AdminOnly,
    start_date: _StartDate = None,
    end_date: _EndDate = None,
) -> dict[str, int]:
    """Cuántos movimientos traería el CSV con ese rango, sin descargarlo."""
    _validate_range(start_date, end_date)
    return {"rows": await service.count_rows(start_date=start_date, end_date=end_date)}


@router.get("/export")
async def export_report(
    service: ReportServiceDep,
    current_user: _AdminOnly,
    start_date: _StartDate = None,
    end_date: _EndDate = None,
    excel: Annotated[
        bool,
        Query(description="Antepone el BOM UTF-8 para que Excel respete las tildes."),
    ] = True,
) -> Response:
    """HU-12-01: Exporta el historial desnormalizado (OLAP-ready) como CSV. ADMIN+."""
    _validate_range(start_date, end_date)
    content = await service.export_csv(
        start_date=start_date, end_date=end_date, excel_compatible=excel
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=inventory_olap_export.csv",
        },
    )
