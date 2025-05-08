#!/usr/bin/env bash

echo "🚀 Reiniciando servicio…"
docker compose -p jmq_chirpstack_listener_dev restart app

echo "✅ Despliegue completado. Logs:"
docker compose -p jmq_chirpstack_listener_dev logs -f app
