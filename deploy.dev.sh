#!/bin/bash

echo "📦 Deteniendo contenedores antiguos... Mete --volumes si quieres borrar los datos antiguos."
docker compose -f docker-compose.dev.yml down
echo "🔧 Construyendo contenedores desde cero (sin caché)..."
docker compose -f docker-compose.dev.yml build --no-cache
echo "🚀 Levantando servicios en segundo plano..."
docker compose -f docker-compose.dev.yml up -d
echo "✅ Despliegue completado. Contenedores activos:"
docker ps
bash entrypoint-dev.sh


