# app/mqtt_client.py  (versión completa)

"""
Cliente MQTT con reconexión automática y soporte TLS opcional.
Escucha uplinks de ChirpStack, almacena los valores numéricos en TimescaleDB
y publica el estado de la conexión a través de app/status.py
"""

from __future__ import annotations

import json
import logging
import os
import ssl
import time
from typing import Any, Dict

import paho.mqtt.client as mqtt

from app.database import SessionLocal
from app.models import SensorData
from app.status import update as update_status

# ───────────────────────── Config ────────────────────────── #

BROKER: str = os.getenv("MQTT_BROKER", "185.43.254.149")
PORT: int = int(os.getenv("MQTT_PORT", "8883"))
KEEPALIVE: int = int(os.getenv("MQTT_KEEPALIVE", "60"))
RETRY_DELAY: int = int(os.getenv("MQTT_RETRY_DELAY", "5"))       # 1er reintento
MAX_DELAY: int = int(os.getenv("MQTT_MAX_DELAY", "60"))          # tope backoff

TOPIC: str = os.getenv("MQTT_TOPIC", "application/+/device/+/event/up")
SYS_TOPIC: str = "$SYS/#"

CTX_DIR = os.getenv("MQTT_CTX_DIR", "/app/ctx")
CA_FILE = os.getenv("MQTT_CA", os.path.join(CTX_DIR, "ca.crt"))
CERT_FILE = os.getenv("MQTT_CERT", os.path.join(CTX_DIR, "cert.crt"))
KEY_FILE = os.getenv("MQTT_KEY", os.path.join(CTX_DIR, "cert.key"))

MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("mqtt_client")

# ──────────────────────── Callbacks ───────────────────────── #

def on_connect(client: mqtt.Client, userdata: Any,
               flags: Dict[str, Any], rc: int):
    icon = "🟢" if rc == 0 else "⚠️"
    logger.info("%s Conectado al broker (rc=%s)", icon, rc)
    update_status(connected=(rc == 0), rc=rc)

    client.subscribe(TOPIC)
    client.subscribe(SYS_TOPIC)
    logger.info("📡 Subscrito a ‘%s’ y ‘%s’", TOPIC, SYS_TOPIC)


def on_disconnect(client: mqtt.Client, userdata: Any, rc: int):
    logger.warning("🔴 Desconectado del broker (rc=%s)", rc)
    update_status(connected=False, rc=rc)


def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
    if msg.topic.startswith("$SYS/"):
        return          # ignoramos mensajes de sistema

    session = SessionLocal()
    try:
        payload = json.loads(msg.payload.decode())
        device_id = (payload.get("devEUI")
                     or payload.get("deviceInfo", {}).get("devEui"))
        ts = (payload.get("receivedAt") or payload.get("time")
              or time.strftime("%Y-%m-%dT%H:%M:%S"))
        object_data = payload.get("objectJSON") or payload.get("object", {})

        for key, value in object_data.items():
            if isinstance(value, (int, float)):
                logger.info("[DB] %s %s %s = %s", device_id, ts, key, value)
                session.add(SensorData(device_id=device_id,
                                       timestamp=ts,
                                       key=key,
                                       value=value))
        session.commit()
    except Exception as exc:        # pragma: no cover
        logger.exception("❌ Error procesando mensaje: %s", exc)
        session.rollback()
    finally:
        session.close()

# ─────────────────────── Helper de cliente ─────────────────── #

def build_client() -> mqtt.Client:
    client = mqtt.Client(protocol=mqtt.MQTTv311)

    if all(os.path.exists(p) for p in (CA_FILE, CERT_FILE, KEY_FILE)):
        client.tls_set(ca_certs=CA_FILE,
                       certfile=CERT_FILE,
                       keyfile=KEY_FILE,
                       tls_version=ssl.PROTOCOL_TLSv1_2)
        logger.info("🔐 TLS habilitado (CA=%s)", CA_FILE)
    else:
        logger.warning("⚠️  TLS deshabilitado: no se encontraron todos los ficheros")

    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD or "")
        logger.info("🛂 Autenticación USER/PASS para ‘%s’", MQTT_USER)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.enable_logger(logger)

    return client

# ───────────────────────── Entry-point ─────────────────────── #

def run() -> None:
    delay = RETRY_DELAY
    client = build_client()

    while True:
        try:
            logger.info("🌐 Conectando a %s:%s …", BROKER, PORT)
            client.connect(BROKER, PORT, keepalive=KEEPALIVE)
            client.loop_forever()
        except (ConnectionRefusedError, OSError) as exc:
            logger.error("❌ Conexión fallida: %s", exc)
            logger.info("↻ Reintentando en %s s…", delay)
            time.sleep(delay)
            delay = min(delay * 2, MAX_DELAY)     # back-off exponencial
        except KeyboardInterrupt:
            logger.info("⏹️  CTRL-C – cerrando conexión…")
            break
        finally:
            try:
                client.disconnect()
            except Exception:
                pass


if __name__ == "__main__":
    run()
