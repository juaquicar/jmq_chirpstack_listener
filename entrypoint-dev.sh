#!/bin/bash
echo "Iniciando el servidor en modo desarrollo REST (con recarga automática)..."
export $(cat .env.dev | grep -v '^#' | xargs)
exec uvicorn $APP_MODULE --host $HOST --port $PORT --reload
