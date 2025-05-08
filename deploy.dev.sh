#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#  Despliega el stack de DESARROLLO con nombres aislados para evitar colisiones
#  con los contenedores/volúmenes/redes del stack de PRODUCCIÓN.
# ------------------------------------------------------------------------------

set -euo pipefail

# Nombre de proyecto que Compose usará como prefijo
DEV_PROJECT="jmq_chirpstack_listener_dev"

echo "📦 Deteniendo contenedores antiguos…"
docker compose \
  -p "${DEV_PROJECT}" \
  -f docker-compose.dev.yml \
  down --remove-orphans

echo "🔧 Construyendo contenedores desde cero (sin caché)…"
docker compose \
  -p "${DEV_PROJECT}" \
  -f docker-compose.dev.yml \
  build --no-cache

echo "🚀 Levantando servicios en segundo plano…"
docker compose \
  -p "${DEV_PROJECT}" \
  -f docker-compose.dev.yml \
  up -d

echo "✅ Despliegue completado. Contenedores activos:"
docker compose \
  -p "${DEV_PROJECT}" \
  -f docker-compose.dev.yml \
  ps
