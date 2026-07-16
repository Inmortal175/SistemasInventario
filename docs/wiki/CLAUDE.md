# Wiki Schema

## Dominio
Desarrollo del sistema **PastryStock Manager** — MVP de gestión de inventario para
pastelerías (FastAPI + Next.js 15). Esta wiki es el segundo cerebro del proyecto:
decisiones de arquitectura, patrones aplicados, convenciones y conocimiento generado
durante el desarrollo. Complementa (no reemplaza) al `CLAUDE.md` raíz del proyecto,
que contiene las instrucciones operativas para el código.

## Estructura de carpetas
- `raw/` — fuentes originales (INMUTABLES — el LLM lee pero nunca modifica)
- `raw/assets/` — imágenes descargadas localmente
- `wiki/fuentes/` — resúmenes de cada fuente ingestada (sesiones, docs, artículos)
- `wiki/entidades/` — proyecto, módulos, servicios, personas, herramientas
- `wiki/conceptos/` — patrones, técnicas, decisiones de arquitectura, metodologías
- `wiki/sintesis/` — comparaciones, análisis, exploraciones guardadas
- `index.md` — catálogo de todas las páginas
- `log.md` — registro cronológico de operaciones

## Formatos de página

### Página de fuente (wiki/fuentes/)
Frontmatter: title, date, source_url, source_path, type, tags
Secciones: Resumen, Ideas clave, Entidades mencionadas, Conceptos relacionados, Citas destacadas, Notas de síntesis

### Página de entidad (wiki/entidades/)
Frontmatter: title, type (proyecto/modulo/servicio/persona/herramienta), tags
Secciones: Descripción, Aparece en [fuentes], Relaciones con otras entidades, Notas

### Página de concepto (wiki/conceptos/)
Frontmatter: title, tags, source_count
Secciones: Definición, Fuentes que lo mencionan, Perspectivas/decisiones, Contradicciones detectadas

### Página de síntesis (wiki/sintesis/)
Frontmatter: title, date, query_origin, tags, fuentes_citadas
Secciones: Pregunta de origen, Síntesis, Fuentes citadas

## Convenciones de naming
- Filenames: kebab-case, en español, sin tildes, sin espacios, minúsculas
  - Bien: `server-components.md`, `autenticacion-jwt-cookies.md`
  - Mal: `Server Components.md`, `AutenticacionJWT.md`
- Títulos (H1): español normal con tildes y mayúsculas apropiadas
- Tags en frontmatter: sin tildes, con guiones (`app-router`, `seguridad`)

## Formato del log
## [YYYY-MM-DD] operacion | Detalle
Tipos de operación: init, ingest, query, lint, update

## Workflow de ingesta preferido
Ingesta supervisada, una fuente a la vez (revisar hallazgos antes de guardar).
El usuario prefiere respuestas en español.
