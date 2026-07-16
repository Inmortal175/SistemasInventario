"""Constantes de claves Redis. Centralizar aquí evita strings mágicos dispersos."""


def category_key(category_id: str) -> str:
    return f"category:{category_id}"


def category_slug_key(slug: str) -> str:
    return f"category:slug:{slug}"


# Lista de todas las categorías activas (índice completo serializado)
CATEGORIES_ACTIVE_INDEX = "categories:active:all"

# Set de nombres de categorías activas — para detección O(1) de duplicados
# sin tocar PostgreSQL cuando Redis está caliente
CATEGORY_NAMES_SET = "categories:names:active"

# Canal Pub/Sub para alertas de stock crítico
ALERT_LOW_STOCK_CHANNEL = "alerts:low_stock"

# Canal Pub/Sub para alertas de vencimiento de lotes (HU-13-03)
ALERT_EXPIRATION_CHANNEL = "alerts:expiration_critical"


# Prefijo para locks pesimistas en movimientos de stock
def stock_lock_key(supply_item_id: str) -> str:
    return f"lock:stock:{supply_item_id}"


# ── Rate limiting de login (HU-04-02) ────────────────────────────────────────
def login_rate_limit_key(ip: str) -> str:
    return f"login:rate_limit:{ip}"


def login_block_key(ip: str) -> str:
    return f"login:blocked:{ip}"


# ── Blacklist de tokens JWT (HU-10-02) ───────────────────────────────────────
def token_blacklist_key(jti_or_token: str) -> str:
    return f"token:blacklist:{jti_or_token}"


# Época de sesión: tokens con iat anterior a este timestamp se rechazan.
# Se usa al restablecer contraseñas para matar sesiones viejas permitiendo el
# nuevo login (a diferencia de la blacklist total de la suspensión).
def token_valid_from_key(user_id: str) -> str:
    return f"token:valid_from:{user_id}"


# ── Índice paginado de insumos (HU-06) ───────────────────────────────────────
def supplies_page_key(
    page: int,
    limit: int,
    category_id: str | None,
    location_id: str | None,
    item_type: str | None = None,
) -> str:
    cat = category_id or "all"
    loc = location_id or "all"
    typ = item_type or "all"
    return f"supplies:page:{page}:{limit}:cat:{cat}:loc:{loc}:type:{typ}"


# Patrón para invalidar todas las páginas cacheadas de insumos tras una mutación
SUPPLIES_PAGE_PATTERN = "supplies:page:*"

# ── KPIs del dashboard (HU-08) ───────────────────────────────────────────────
DASHBOARD_KPIS_KEY = "dashboard:kpis"

# ── Identidad visual del sistema (nombre, logo, tema) ────────────────────────
# Se lee en cada render del layout, así que va cacheada; se invalida al guardar.
SYSTEM_SETTINGS_KEY = "settings:system"
