#!/bin/bash
echo "Iniciando el servidor en modo desarrollo (con recarga automática)..."
exec uvicorn main:app --host 0.0.0.0 --port 8999 --reload