import re
from dataclasses import dataclass

from app.domain.exceptions import LocationCodeInvalidError
from app.domain.enums import LocationType, LOCATION_PREFIX_MAP

# Patrón: PREFIJO-NN o PREFIJO-NN-FN
# Prefijos: EST | REF | FRZ | CAB | CON | ALM
# NN: dos dígitos obligatorios (01–99)
# -FN: fila opcional, uno o dos dígitos (solo EST admite fila)
_LOCATION_PATTERN = re.compile(
    r"^(EST|REF|FRZ|CAB|CON|ALM)-(\d{2})(-F(\d{1,2}))?$"
)

# Solo los estantes admiten el sufijo de fila
_SUPPORTS_ROW = {"EST"}


@dataclass(frozen=True)
class LocationCode:
    """Value Object que encapsula y valida el código de ubicación física.

    Ejemplos válidos:
        EST-01       → Estante 1
        EST-01-F2    → Estante 1, Fila 2
        REF-02       → Refrigeradora 2
        FRZ-01       → Congeladora 1
        CAB-03-F1    → (inválido: solo EST admite fila)
    """

    value: str

    def __post_init__(self) -> None:
        match = _LOCATION_PATTERN.match(self.value)
        if not match:
            raise LocationCodeInvalidError(self.value)

        prefix = match.group(1)
        has_row = match.group(3) is not None

        # El patrón admite \d{2}, pero la posición 00 no existe físicamente (rango 01–99).
        if int(match.group(2)) < 1:
            raise LocationCodeInvalidError(self.value)

        if has_row:
            if prefix not in _SUPPORTS_ROW:
                raise LocationCodeInvalidError(self.value)
            # Fila 0 tampoco existe: las filas se rotulan desde F1.
            if int(match.group(4)) < 1:
                raise LocationCodeInvalidError(self.value)

    @property
    def prefix(self) -> str:
        return self.value.split("-")[0]

    @property
    def number(self) -> int:
        return int(self.value.split("-")[1])

    @property
    def row(self) -> int | None:
        parts = self.value.split("-")
        if len(parts) == 3 and parts[2].startswith("F"):
            return int(parts[2][1:])
        return None

    @property
    def location_type(self) -> LocationType:
        return LOCATION_PREFIX_MAP[self.prefix]

    @classmethod
    def parse(cls, raw: str) -> "LocationCode":
        """Factory: normaliza a mayúsculas antes de validar."""
        return cls(value=raw.strip().upper())

    def __str__(self) -> str:
        return self.value
