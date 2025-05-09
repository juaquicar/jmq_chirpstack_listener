# mqtt_debug.py
import os
import ssl
import time
import json
import logging
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "185.43.254.149")
PORT = int(os.getenv("MQTT_PORT", "8883"))
TOPIC = os.getenv("MQTT_TOPIC", "application/+/device/+/event/up")
KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", 60))

CTX_DIR = os.getenv("MQTT_CTX_DIR", "app/ctx/fenix")
CA_FILE = os.getenv("MQTT_CA", os.path.join(CTX_DIR, "ca.crt"))
CERT_FILE = os.getenv("MQTT_CERT", os.path.join(CTX_DIR, "cert.crt"))
KEY_FILE = os.getenv("MQTT_KEY", os.path.join(CTX_DIR, "cert.key"))

print(CA_FILE, CERT_FILE, KEY_FILE)

MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger("mqtt_debug")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("🟢 Conectado al broker MQTT (%s:%d)", BROKER, PORT)
        client.subscribe(TOPIC)
        logger.info("📡 Subscrito al tópico: %s", TOPIC)
    else:
        logger.error("❌ Error de conexión. Código rc=%s", rc)


def on_message(client, userdata, msg):
    logger.info("📨 Mensaje recibido:")
    logger.info("📍 Topic: %s", msg.topic)
    try:
        payload = json.loads(msg.payload.decode())
        logger.info("📦 Payload:\n%s", json.dumps(payload, indent=2))
    except Exception as e:
        logger.error("❌ No se pudo parsear JSON: %s", e)


def main():
    client = mqtt.Client(protocol=mqtt.MQTTv311)

    if all(os.path.exists(p) for p in (CA_FILE, CERT_FILE, KEY_FILE)):
        client.tls_set(ca_certs=CA_FILE,
                       certfile=CERT_FILE,
                       keyfile=KEY_FILE,
                       tls_version=ssl.PROTOCOL_TLSv1_2)
        logger.info("🔐 TLS habilitado con certificados")
    else:
        logger.warning("⚠️ TLS deshabilitado: certificados no encontrados")

    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD or "")
        logger.info("🛂 Autenticación con usuario")

    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("🌐 Conectando a %s:%s …", BROKER, PORT)
    client.connect(BROKER, PORT, KEEPALIVE)
    client.loop_forever()


if __name__ == "__main__":
    main()
