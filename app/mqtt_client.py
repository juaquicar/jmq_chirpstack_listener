import os
import time
import json
import paho.mqtt.client as mqtt
from app.database import SessionLocal
from app.models import SensorData

def on_connect(client, userdata, flags, rc):
    print("🟢 Connected with result code", str(rc))
    client.subscribe("application/+/device/+/event/up")

def on_disconnect(client, userdata, rc):
    print("🔴 Disconnected with result code", str(rc))

def on_message(client, userdata, msg):
    print(f"📨 Mensaje recibido en topic: {msg.topic}")
    print(f"🧾 Payload recibido: {msg.payload.decode()}")

    session = SessionLocal()
    try:
        payload = json.loads(msg.payload.decode())
        device_id = payload.get("devEUI")
        ts = payload.get("receivedAt", "").split('.')[0]
        object_data = payload.get("objectJSON", {})

        for key, value in object_data.items():
            if isinstance(value, (int, float)):
                print(f"[DB] Guardando: {device_id}, {ts}, {key}, {value}")
                data = SensorData(
                    device_id=device_id,
                    timestamp=ts,
                    key=key,
                    value=value
                )
                session.add(data)
        session.commit()
    except Exception as e:
        print("❌ Error al procesar mensaje:", e)
    finally:
        session.close()

def run():
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    broker_host = os.getenv("MQTT_BROKER", "localhost")
    broker_port = int(os.getenv("MQTT_PORT", 1883))
    print(f"🌐 Conectando a broker MQTT en {broker_host}:{broker_port}")

    rc = client.connect(broker_host, broker_port, 60)
    print(f"🚀 Resultado de connect(): {rc}")

    client.loop_start()

    while not client.is_connected():
        print("⏳ Esperando conexión MQTT...")
        time.sleep(1)

    print("✅ Conectado, esperando mensajes...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Parando cliente MQTT...")
        client.disconnect()
        client.loop_stop()

# 🔒 Solo ejecuta si es script principal
if __name__ == "__main__":
    run()
