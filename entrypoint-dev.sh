#!/bin/bash
# entrypoint-dev.sh
set -e
echo "🚀 Iniciando servidor en modo desarrollo (hot-reload)..."

# Carga variables de entorno desde .env.dev si existe
if [ -f env.dev ]; then
  export $(grep -v '^\s*#' env.dev | xargs)
fi

# Valores por defecto si no se han definido en .env.dev
: "${APP_MODULE:=app.main:app}"
: "${HOST:=0.0.0.0}"
: "${PORT:=8999}"

exec uvicorn $APP_MODULE --host $HOST --port $PORT --reload
