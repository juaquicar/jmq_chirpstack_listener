#!/bin/bash

echo "🚀 Publicando mensaje MQTT de prueba..."

mosquitto_pub -h localhost -p 1884 -t "application/1/device/abcd1234/event/up" -m '{
  "devEUI": "abcd1234",
  "receivedAt": "2025-04-16T04:00:00.000Z",
  "objectJSON": {
    "temperature": 22.8,
    "humidity": 58
  }
}'

echo "⏳ Esperando procesamiento..."
sleep 2

echo "🔎 Consultando base de datos TimescaleDB..."

DB_NAME=${DB_NAME:-sensordata}
DB_USER=${DB_USER:-sensoruser}

docker exec -it chirpstack_listener_app python -m app.init_db
docker exec -it chirpstack_timescaledb \
psql -U "$DB_USER" -d "$DB_NAME" \
-c "SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 5;"

echo "🌐 Probando endpoint API..."
curl -s "http://localhost:8999/data/" | jq .
