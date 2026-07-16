"""Iconos que una categoría dinámica puede usar.

Los slugs son agnósticos del set de iconos: el frontend traduce cada uno a un
SVG en `src/lib/categoryIcons.ts`. Esa tabla y esta lista deben cambiar juntas,
o el selector ofrecerá iconos que la API rechaza.
"""

ALLOWED_CATEGORY_ICONS: frozenset[str] = frozenset({
    # Pastelería y panadería
    "cake", "cookie", "bread", "wheat", "ice-cream", "candy",
    # Lácteos, proteínas y frescos
    "cheese", "egg", "milk", "meat", "bacon", "fish",
    # Frutas, verduras y especias
    "apple", "lemon", "carrot", "pepper", "seedling", "leaf",
    # Bebidas y envases
    "mug", "bottle", "wine", "jar", "bowl", "pizza",
    # Herramientas de cocina
    "utensils", "kitchen", "blender", "scale", "fire", "snowflake",
    # Útiles de limpieza y almacén
    "box", "broom", "soap", "spray", "tools",
    # Genéricos
    "tag", "star", "heart",
})
