# ChirpStack Listener App

Microservicio que escucha mensajes MQTT desde ChirpStack, guarda los datos en TimescaleDB y expone endpoints de consulta vía FastAPI.

---

## 🧩 Requisitos

- Docker
- Docker Compose

### Instalar en Ubuntu Server

```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

Cierra sesión y vuelve a entrar para que los cambios de grupo surtan efecto.

---

## 🚀 Despliegue en producción

```bash
sudo bash deploy.sh
```

La API estará disponible en: `http://localhost:8999`

---

## ⚙️ Variables de entorno necesarias

Definir en `.env.production`:

```env
# Entorno
ENV=production

# Base de datos
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=

# MQTT
MQTT_BROKER=
MQTT_PORT=
MQTT_TOPIC=application/1/device/+/event/up

# Puerto API
APP_MODULE=app.main:app
PORT=8999
HOST=0.0.0.0
API_HOST=0.0.0.0
WORKERS=2
```

---

## 📦 Estructura del proyecto

- `app/` — Código fuente principal
  - `main.py` — App FastAPI
  - `mqtt_client.py` — Cliente MQTT y lógica de ingestión
  - `models.py`, `schemas.py` — Modelos
  - `database.py` — Conexión con TimescaleDB
- `tests/` — Scripts de prueba de publicación MQTT y verificación de API
- `entrypoint-prod.sh` — Script de arranque para producción
- `entrypoint-dev.sh` — Script de arranque para desarrollo

---

## Instalar

```bash
sudo bash deploy.sh
```




## 🧪 Pruebas

```bash
cd tests
./mqtt_test.sh
```

---

## 🌐 Endpoints disponibles

- `GET /health`: Comprobación de estado.
- `GET /measurements/?device_id=&start=&end=`: Lista de medidas crudas por dispositivo y fecha.
- `GET /latest_measurements/?device_id=`: Última medida de cada tipo (key) por dispositivo.
- `GET /latest_measurements_grouped/?device_id=`: Últimas medidas agrupadas por clave.
- `GET /timeseries/?device_id=&key=&start=&end=`: Serie temporal completa de un tipo de medida.
- `GET /timeseries/aggregated/?device_id=&key=&start=&end=&interval=`: Medidas agregadas por hora, día o semana.
- `GET /timeseries/aggregated/full/?device_id=&key=&start=&end=&interval=`: Agregadas con media, máximo y mínimo.
- `GET /timeseries/aggregated/multi/?device_ids=&key=&start=&end=&interval=`: Agregadas para múltiples dispositivos.

### 🔁 Parámetros de intervalo permitidos

- `interval=hour` (por defecto)
- `interval=day`
- `interval=week`

---

## 📄 Especificación de la API

- `GET /openapi.json`: Especificación de la API en formato OpenAPI 3 (compatible Swagger y Postman)

---

## 📬 Ejemplo de mensaje MQTT procesado

```json
{
  "devEUI": "abc123",
  "receivedAt": "2025-04-16T10:00:00.000Z",
  "objectJSON": {
    "temperature": 21.5,
    "humidity": 45.3
  }
}
```

Cada clave en `objectJSON` se almacena como una fila independiente con su `key`, `value`, `timestamp` y `device_id`.

---

## 📝 Notas

- Requiere que ChirpStack esté enviando datos a un broker MQTT accesible.
- El cliente MQTT se conecta al host `mosquitto` (ajustar si es necesario).
- El microservicio debe estar configurado para apuntar a las variables correctas en producción.

---

Desarrollado con ❤️ por Juanma Quijada