#!/bin/bash
# deploy.sh - Automatiza el despliegue en producción
# Asegúrate de dar permisos de ejecución:
# chmod +x deploy.sh

echo "📦 Deteniendo contenedores antiguos..."
docker compose -f docker-compose.production.yml down
echo "🔧 Construyendo contenedores desde cero (sin caché)..."
docker compose -f docker-compose.production.yml build --no-cache
echo "🚀 Levantando servicios en segundo plano..."
docker compose -f docker-compose.production.yml up -d
echo "✅ Despliegue completado. Contenedores activos:"
docker ps


