#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#  Entrypoint del contenedor de FastAPI en modo DESARROLLO (hot-reload)
# ------------------------------------------------------------------------------

set -euo pipefail
echo "🚀 Iniciando servidor en modo desarrollo (hot-reload)…"

# Carga variables de entorno desde env.dev si existe
if [[ -f env.dev ]]; then
  # shellcheck disable=SC2046
  export $(grep -vE '^[[:space:]]*#' env.dev | xargs)
fi

# Valores por defecto si no se han definido en env.dev
: "${APP_MODULE:=app.main:app}"
: "${HOST:=0.0.0.0}"
: "${PORT:=8999}"

exec python3 -m uvicorn "${APP_MODULE}" \
     --host "${HOST}" \
     --port "${PORT}" \
     --reload
