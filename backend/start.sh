#!/bin/sh
# Arranque del backend en producción.
#
# Las migraciones NO deben poder impedir que la app levante: si alembic se
# cuelga (p. ej. esperando un lock), con `&&` secuestraría la ventana del
# healthcheck y Railway mataría el contenedor sin un solo error en los logs.
# Con el timeout y sin `set -e`, un fallo aquí se anuncia y el arranque sigue.

# El Volume de Railway se monta como root y vacío, tapando el static/ que creó
# el Dockerfile. Por eso el servicio necesita RAILWAY_RUN_UID=0: arrancamos como
# root solo para reparar los permisos del punto de montaje y bajamos a appuser
# antes de servir nada. Sin esto, las subidas fallarían con EACCES; corriendo
# todo como root, la app tendría privilegios que no necesita.
if [ "$(id -u)" = "0" ]; then
    echo "==> root: preparando /app/static y bajando a appuser..."
    mkdir -p /app/static/avatars /app/static/branding
    chown -R appuser:appgroup /app/static
    exec setpriv --reuid=appuser --regid=appgroup --init-groups sh "$0" "$@"
fi

echo "==> Aplicando migraciones (máx. 90s)..."
if timeout 90 alembic upgrade head; then
    echo "==> Migraciones al día."
else
    echo "!!! ALEMBIC FALLO O SUPERO LOS 90s — la app arranca igual."
    echo "!!! Revisar a mano con: railway run alembic upgrade head"
fi

echo "==> Iniciando gunicorn en el puerto ${PORT:-8000} como $(id -un)..."
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind "0.0.0.0:${PORT:-8000}" \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info
