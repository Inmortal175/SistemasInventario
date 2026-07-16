from enum import Enum


class UserRole(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    STAFF = "STAFF"


class ThemeName(str, Enum):
    """Paletas de color del sistema. Se persiste como texto, no como ENUM de PG:
    agregar una paleta no debería requerir migrar un tipo en la base."""
    ROSA = "rosa"
    CHOCOLATE = "chocolate"
    MENTA = "menta"
    AZUL = "azul"


class LoginBackgroundDevice(str, Enum):
    """Fondos del login. Los cortes coinciden con los breakpoints `md`/`lg` de
    Tailwind, que es donde el resto de la interfaz ya cambia de forma."""
    MOBILE = "mobile"      # < 768px
    TABLET = "tablet"      # 768–1023px
    DESKTOP = "desktop"    # >= 1024px


# Relación de aspecto y tamaño de salida de cada fondo.
LOGIN_BACKGROUND_SIZES: dict[LoginBackgroundDevice, tuple[int, int]] = {
    LoginBackgroundDevice.MOBILE: (720, 1280),    # 9:16 vertical
    LoginBackgroundDevice.TABLET: (900, 1200),    # 3:4 vertical
    LoginBackgroundDevice.DESKTOP: (1920, 1080),  # 16:9 horizontal
}


class MovementType(str, Enum):
    ENTRY = "ENTRY"                 # Ingreso de stock — ADMIN+
    EXIT = "EXIT"                   # Consumo/retiro   — STAFF+
    ADJUSTMENT_ADD = "ADJUSTMENT_ADD"   # Ajuste positivo  — ADMIN+
    ADJUSTMENT_SUB = "ADJUSTMENT_SUB"   # Ajuste negativo  — ADMIN+
    WASTE = "WASTE"                 # Merma/descarte   — STAFF+
    TRANSFER = "TRANSFER"           # Traslado físico  — ADMIN+


class ItemType(str, Enum):
    """Distingue insumos (materia prima) de productos terminados. Se persiste como
    texto (no como ENUM de PG): un `supply_item` sirve para ambos y así reutiliza
    stock, lotes FIFO, vencimiento, movimientos y valorización (HU-17)."""
    INGREDIENT = "INGREDIENT"           # Materia prima que se consume
    FINISHED_PRODUCT = "FINISHED_PRODUCT"   # Producto elaborado que se produce y vende


class UnitMeasure(str, Enum):
    KG = "KG"
    GR = "GR"
    L = "L"
    ML = "ML"
    UNIT = "UNIT"
    PKG = "PKG"
    BOX = "BOX"
    DOZEN = "DOZEN"


class LocationType(str, Enum):
    SHELF = "SHELF"             # Estante      — código EST-XX[-FX]
    REFRIGERATOR = "REFRIGERATOR"   # Refrigeradora — código REF-XX
    FREEZER = "FREEZER"         # Congeladora  — código FRZ-XX
    CABINET = "CABINET"         # Armario      — código CAB-XX
    COUNTER = "COUNTER"         # Mostrador    — código CON-XX
    WAREHOUSE = "WAREHOUSE"     # Almacén      — código ALM-XX


# Movimientos que cada rol tiene permitido registrar
ALLOWED_MOVEMENTS_BY_ROLE: dict[UserRole, set[MovementType]] = {
    UserRole.STAFF: {MovementType.EXIT, MovementType.WASTE},
    UserRole.ADMIN: set(MovementType),       # todos
    UserRole.SUPERADMIN: set(MovementType),  # todos
}

# Prefijos de código válidos por tipo de ubicación
LOCATION_PREFIX_MAP: dict[str, LocationType] = {
    "EST": LocationType.SHELF,
    "REF": LocationType.REFRIGERATOR,
    "FRZ": LocationType.FREEZER,
    "CAB": LocationType.CABINET,
    "CON": LocationType.COUNTER,
    "ALM": LocationType.WAREHOUSE,
}
