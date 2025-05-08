#!/usr/bin/env bash
# tests/publish_weather_station.sh
# ──────────────────────────────────────────────────────────────────────────────
#  Publica un uplink simulado de una Estación Meteorológica en el broker MQTT
#  de DESARROLLO (mosquitto_dev) y muestra los últimos valores servidos por la
#  API FastAPI tras almacenarse en TimescaleDB.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

BROKER_HOST=${BROKER_HOST:-localhost}
BROKER_PORT=${BROKER_PORT:-1884}
TOPIC="application/1/device/2cf7f1c0443000f2/event/up"

echo "🚀 Publicando mensaje en  mqtt://${BROKER_HOST}:${BROKER_PORT}/${TOPIC}"

mosquitto_pub -h "$BROKER_HOST" -p "$BROKER_PORT" -t "$TOPIC" -m '{
  "deduplicationId":"1d4301a8-7f65-438b-8115-c7e6915ba86d",
  "time":"2025-05-08T16:26:07.887+00:00",
  "deviceInfo":{
    "tenantId":"52f14cd4-c6f1-4fbd-8f87-4025e1d49242",
    "tenantName":"ChirpStack",
    "applicationId":"b2fe8cb4-c95a-4a4c-a354-c2bf470d61eb",
    "applicationName":"Sensores",
    "deviceProfileId":"fcf607dc-3f2f-4401-9df4-571cf9e65452",
    "deviceProfileName":"estacion-meteorologica-profile",
    "deviceName":"Estacion Meteorologica",
    "devEui":"2cf7f1c0443000f2",
    "deviceClassEnabled":"CLASS_A",
    "tags":{}
  },
  "devAddr":"01a0e7a8",
  "adr":true,
  "dr":5,
  "fCnt":5586,
  "fPort":3,
  "confirmed":true,
  "data":"SgDIMwAAb64MAChLAGUAAAAAJtlMAFwAARnI",
  "object":{
    "Pico_Velocidad_Viento":9.2,
    "Humedad":51.0,
    "Velocidad_Viento":4.0,
    "Presion":99450.0,
    "Indice_UltraVioleta":1.2,
    "Lluvia_Acumulada":72.136,
    "Intensidad_Lluvia":0.0,
    "Direccion_Viento":101.0,
    "Luz":28590.0,
    "Temperatura":20.0
  },
  "rxInfo":[
    {
      "gatewayId":"00800000a00028a6",
      "uplinkId":30895,
      "gwTime":"2025-05-08T16:26:07.887935+00:00",
      "nsTime":"2025-05-08T16:26:07.899399767+00:00",
      "timeSinceGpsEpoch":"1430756785.887s",
      "rssi":-42,
      "snr":8.5,
      "channel":5,
      "rfChain":1,
      "location":{"latitude":37.73072,"longitude":-5.11428,"altitude":169.0},
      "context":"vIjHjA==",
      "crcStatus":"CRC_OK"
    }
  ],
  "txInfo":{
    "frequency":867500000,
    "modulation":{
      "lora":{"bandwidth":125000,"spreadingFactor":7,"codeRate":"CR_4_5"}
    }
  },
  "regionConfigId":"eu868"
}'

echo "⏳ Esperando a que el listener procese el mensaje…"
sleep 2   # pequeño margen para la inserción en la BD

API_URL=${API_URL:-http://localhost:8999}
DEVICE_ID="2cf7f1c0443000f2"

echo "🌐 Últimas mediciones agrupadas para el dispositivo $DEVICE_ID:"
curl -s "${API_URL}/latest_measurements_grouped/?device_id=${DEVICE_ID}" | jq .

echo "✅ Test completado."
