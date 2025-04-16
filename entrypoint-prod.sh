#!/bin/bash
set -e
echo "🚀 Iniciando el servicio en modo PRODUCCIÓN..."
LOG_DIR="/var/log"
API_LOG="${LOG_DIR}/api.err.log"
mkdir -p "$LOG_DIR"
touch "$API_LOG"

HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8999}
WORKERS=${WORKERS:-2}
APP_MODULE=${APP_MODULE:-main:app}

if [ -z "$WORKERS" ]; then
  echo "❌ ERROR: Variable WORKERS no está definida. ¿Cargaste el .env.production?"
  exit 1
fi

gunicorn "$APP_MODULE" --workers "$WORKERS" --worker-class uvicorn.workers.UvicornWorker \
  --bind "$HOST:$PORT" --log-level debug --access-logfile "$API_LOG" --error-logfile "$API_LOG" || true

tail -f /dev/null
