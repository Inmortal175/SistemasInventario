# ═══════════════════════════════════════════════
#  Backend — FastAPI
#  Multi-stage: development | production
# ═══════════════════════════════════════════════

# ── Imagen base compartida ──────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema necesarias para asyncpg y psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Stage: dependencias de producción ──────────
FROM base AS deps-prod

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage: desarrollo (hot-reload) ─────────────
FROM deps-prod AS development

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# El código se monta como volumen en docker-compose
# No se hace COPY aquí para preservar el hot-reload
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Stage: producción ───────────────────────────
FROM deps-prod AS production

COPY . .

# Crear usuario no-root para producción
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

# Workers = 2 * CPU + 1 (ajustar según recursos)
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "3", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keep-alive", "5"]
