"""
app/mqtt_client.py

Listener MQTT para ChirpStack con soporte TLS.
Lee las rutas de certificados, credenciales y topic desde variables de entorno.

Variables importantes (con sus valores por defecto):

MQTT_BROKER   = 185.43.254.149
MQTT_PORT     = 8883
MQTT_CA       = /app/ctx/ca.crt
MQTT_CERT     = /app/ctx/cert.crt
MQTT_KEY      = /app/ctx/cert.key
MQTT_USER     = (vacío)
MQTT_PASSWORD = (vacío)
MQTT_TOPIC    = application/+/device/+/event/up
"""

import json
import os
import ssl
import time

import paho.mqtt.client as mqtt
from app.database import SessionLocal
from app.models import SensorData

# --------------------------------------------------------------------------- #
#  Callbacks
# --------------------------------------------------------------------------- #


def on_connect(client, userdata, flags, rc):
    status = "🟢" if rc == 0 else "⚠️"
    print(f"{status} Connected with result code {rc}")
    topic = os.getenv("MQTT_TOPIC", "application/+/device/+/event/up")
    client.subscribe(topic)
    print(f"📡 Subscribed to «{topic}»")


def on_disconnect(client, userdata, rc):
    print(f"🔴 Disconnected with result code {rc}")


def on_message(client, userdata, msg):
    print(f"📨 Mensaje recibido en topic: {msg.topic}")
    print(f"🧾 Payload recibido: {msg.payload.decode()}")

    session = SessionLocal()
    try:
        payload = json.loads(msg.payload.decode())
        device_id = payload.get("devEUI")
        ts = payload.get("receivedAt", "").split(".")[0]
        object_data = payload.get("objectJSON", {})

        for key, value in object_data.items():
            if isinstance(value, (int, float)):
                print(f"[DB] Guardando: {device_id}, {ts}, {key}, {value}")
                data = SensorData(
                    device_id=device_id,
                    timestamp=ts,
                    key=key,
                    value=value,
                )
                session.add(data)
        session.commit()
    except Exception as e:
        print("❌ Error al procesar mensaje:", e)
    finally:
        session.close()


# --------------------------------------------------------------------------- #
#  Configuración del cliente
# --------------------------------------------------------------------------- #


def build_client() -> mqtt.Client:
    client = mqtt.Client(protocol=mqtt.MQTTv311)

    # --- TLS ---------------------------------------------------------------
    ca_path = os.getenv("MQTT_CA", "/app/ctx/ca.crt")
    cert_path = os.getenv("MQTT_CERT", "/app/ctx/cert.crt")
    key_path = os.getenv("MQTT_KEY", "/app/ctx/cert.key")

    if all(map(os.path.exists, (ca_path, cert_path, key_path))):
        client.tls_set(
            ca_certs=ca_path,
            certfile=cert_path,
            keyfile=key_path,
            tls_version=ssl.PROTOCOL_TLSv1_2,
        )
        print(f"🔐 TLS habilitado (CA: {ca_path})")
    else:
        print("⚠️  No se encontraron los ficheros TLS — conexión sin cifrar")

    # --- Credenciales opcionales ------------------------------------------
    user = os.getenv("MQTT_USER")
    pwd = os.getenv("MQTT_PASSWORD")
    if user:
        client.username_pw_set(user, pwd or "")
        print(f"🛂 Usando autenticación de usuario «{user}»")

    # --- Callbacks ---------------------------------------------------------
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    return client


# --------------------------------------------------------------------------- #
#  Loop principal
# --------------------------------------------------------------------------- #


def run() -> None:
    client = build_client()

    broker_host = os.getenv("MQTT_BROKER", "185.43.254.149")
    broker_port = int(os.getenv("MQTT_PORT", 8883))
    print(f"🌐 Conectando a broker MQTT en {broker_host}:{broker_port}")

    client.connect(broker_host, broker_port, keepalive=60)
    client.loop_start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Parando cliente MQTT…")
        client.disconnect()
        client.loop_stop()


# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    run()
