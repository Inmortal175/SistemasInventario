from pydantic import BaseModel


class TopWastedSupply(BaseModel):
    supply_id: str
    supply_name: str
    total_wasted: str


class KpisResponse(BaseModel):
    """HU-08-01: métricas consolidadas del dashboard."""

    total_critical_items: int
    movements_last_24h: int
    top_wasted_supplies: list[TopWastedSupply]
    source: str = "database"      # "cache" | "database"
