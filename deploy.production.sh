#!/bin/bash
# deploy.production.sh - Automatiza el despliegue en producción
# Asegúrate de dar permisos de ejecución:
# chmod +x deploy.production.sh

echo "📦 Deteniendo contenedores antiguos... Mete --volumes si quieres borrar los datos antiguos."
docker compose -f docker-compose.production.yml down
echo "🔧 Construyendo contenedores desde cero (sin caché)..."
docker compose -f docker-compose.production.yml build --no-cache
echo "🚀 Levantando servicios en segundo plano..."
docker compose -f docker-compose.production.yml up -d
echo "✅ Despliegue completado. Contenedores activos:"
docker ps

echo "🔧 Mostrando LOG"
#docker exec -it chirpstack_listener_app tail -f /var/log/api.err.log
docker logs -f chirpstack_listener_app
