#!/bin/sh
# Arranque del backend en producción.
#
# Las migraciones NO deben poder impedir que la app levante: si alembic se
# cuelga (p. ej. esperando un lock), con `&&` secuestraría la ventana del
# healthcheck y Railway mataría el contenedor sin un solo error en los logs.
# Con el timeout y sin `set -e`, un fallo aquí se anuncia y el arranque sigue.

echo "==> Aplicando migraciones (máx. 90s)..."
if timeout 90 alembic upgrade head; then
    echo "==> Migraciones al día."
else
    echo "!!! ALEMBIC FALLO O SUPERO LOS 90s — la app arranca igual."
    echo "!!! Revisar a mano con: railway run alembic upgrade head"
fi

echo "==> Iniciando gunicorn en el puerto ${PORT:-8000}..."
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind "0.0.0.0:${PORT:-8000}" \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info
