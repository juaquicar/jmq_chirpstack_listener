# app/mqtt_client.py
"""
Cliente MQTT con soporte TLS (opcional).
Escucha uplinks de ChirpStack, almacena los valores numéricos
en TimescaleDB y publica el estado de la conexión a través de
app/status.py
"""

from __future__ import annotations

import json
import os
import ssl
import time
import logging
from typing import Any, Dict

import paho.mqtt.client as mqtt

from app.database import SessionLocal
from app.models import SensorData
from app.status import update as update_status

# --------------------------------------------------------------------------- #
#  Configuración
# --------------------------------------------------------------------------- #

BROKER: str = os.getenv("MQTT_BROKER", "185.43.254.149")
PORT: int = int(os.getenv("MQTT_PORT", "8883"))
KEEPALIVE: int = int(os.getenv("MQTT_KEEPALIVE", "60"))

# Suscripción principal y de sistema
TOPIC: str = os.getenv("MQTT_TOPIC", "application/+/device/+/event/up")
SYS_TOPIC: str = "$SYS/#"

# Directorio por defecto donde montaremos los certificados dentro del contenedor
CTX_DIR = os.getenv("MQTT_CTX_DIR", "/app/ctx")
CA_FILE = os.getenv("MQTT_CA", os.path.join(CTX_DIR, "ca.crt"))
CERT_FILE = os.getenv("MQTT_CERT", os.path.join(CTX_DIR, "cert.crt"))
KEY_FILE = os.getenv("MQTT_KEY", os.path.join(CTX_DIR, "cert.key"))

# Credenciales opcionales
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("mqtt_client")

# --------------------------------------------------------------------------- #
#  Callbacks
# --------------------------------------------------------------------------- #


def on_connect(client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int):
    icon = "🟢" if rc == 0 else "⚠️"
    logger.info("%s Conectado al broker (rc=%s)", icon, rc)
    update_status(connected=(rc == 0), rc=rc)

    # Suscribirse a los tópicos
    client.subscribe(TOPIC)
    client.subscribe(SYS_TOPIC)
    logger.info("📡 Subscrito a ‘%s’ y ‘%s’", TOPIC, SYS_TOPIC)


def on_disconnect(client: mqtt.Client, userdata: Any, rc: int):
    logger.warning("🔴 Desconectado del broker (rc=%s)", rc)
    update_status(connected=False, rc=rc)


def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
    logger.debug("📨 Mensaje en %s", msg.topic)

    # Solo procesamos los uplinks. Filtra $SYS/# u otros tópicos.
    if msg.topic.startswith("$SYS/"):
        return

    session = SessionLocal()
    try:
        payload = json.loads(msg.payload.decode())
        device_id = payload.get("devEUI") or payload.get("deviceInfo", {}).get("devEui")
        ts = (
            payload.get("receivedAt")
            or payload.get("time")
            or time.strftime("%Y-%m-%dT%H:%M:%S")
        )
        object_data = payload.get("objectJSON") or payload.get("object", {})

        # Persistir únicamente valores numéricos
        for key, value in object_data.items():
            if isinstance(value, (int, float)):
                logger.info("[DB] %s %s %s = %s", device_id, ts, key, value)
                session.add(
                    SensorData(
                        device_id=device_id,
                        timestamp=ts,
                        key=key,
                        value=value,
                    )
                )
        session.commit()
    except Exception as exc:  # pragma: no cover
        logger.exception("❌ Error procesando mensaje: %s", exc)
        session.rollback()
    finally:
        session.close()

# --------------------------------------------------------------------------- #
#  Cliente helper
# --------------------------------------------------------------------------- #


def build_client() -> mqtt.Client:
    """Configura y devuelve un cliente MQTT listo para usar."""

    client = mqtt.Client(protocol=mqtt.MQTTv311)

    # TLS ------------------------------------------------------------
    if all(os.path.exists(p) for p in (CA_FILE, CERT_FILE, KEY_FILE)):
        client.tls_set(
            ca_certs=CA_FILE,
            certfile=CERT_FILE,
            keyfile=KEY_FILE,
            tls_version=ssl.PROTOCOL_TLSv1_2,
        )
        logger.info("🔐 TLS habilitado (CA=%s)", CA_FILE)
    else:
        logger.warning("⚠️  TLS deshabilitado: no se encontraron todos los ficheros")

    # Credenciales opcionales ---------------------------------------
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD or "")
        logger.info("🛂 Autenticación USER/PASS activada para el usuario ‘%s’", MQTT_USER)

    # Callbacks ------------------------------------------------------
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Habilitar log interno de paho (útil para debug)
    client.enable_logger(logger)
    return client


# --------------------------------------------------------------------------- #
#  Entry point
# --------------------------------------------------------------------------- #


def run() -> None:
    """Función de arranque que se usará en un hilo o como __main__."""

    client = build_client()
    logger.info("🌐 Conectando a %s:%s …", BROKER, PORT)
    client.connect(BROKER, PORT, keepalive=KEEPALIVE)

    client.loop_start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("⏹️  CTRL‑C – cerrando conexion…")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
