# 🐳 Desarrollo y Pruebas del Microservicio Dockerizado

Este documento contiene comandos útiles para trabajar con el entorno de desarrollo del listener MQTT integrado con TimescaleDB y FastAPI.

---

## 🔄 Reinicio y Montaje del Docker

```bash
sudo docker compose down
sudo docker compose up --build
```

O para levantarlo en segundo plano:

```bash
sudo docker compose up -d
```

---

## 🔧 Forzar una Reconstrucción Completa

```bash
sudo docker compose down --volumes
sudo docker compose build --no-cache
sudo docker compose up
```

---

## 🐍 Logs del Listener

### Ver errores del servidor **FastAPI**
```bash
sudo docker exec -it chirpstack_listener_app cat /var/log/api.err.log
```

### Ver errores del cliente **MQTT**
```bash
sudo docker exec -it chirpstack_listener_app cat /var/log/mqtt.err.log
```

---

## 🧹 Limpieza Profunda de Docker

```bash
sudo docker stop $(docker ps -q)
sudo docker rm $(docker ps -aq)
sudo docker volume prune -f
sudo docker network prune -f
```

---

## 🌲 Árbol de directorios (nivel 2)

```bash
tree . -L 2
```

---

## 📡 Enviar un Mensaje de Prueba vía MQTT

```bash
mosquitto_pub -h localhost -p 1884 -t "application/1/device/abcd1234/event/up" -m '{
  "devEUI": "abcd1234",
  "receivedAt": "2025-04-16T03:37:00.000Z",
  "objectJSON": {
    "temperature": 23.4,
    "humidity": 60
  }
}'
```

---

## 🗃️ Consultar la Base de Datos (TimescaleDB)

```bash
sudo docker exec -it chirpstack_timescaledb psql -U sensoruser -d sensordata -c "SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;"
```

---

## 📜 Ver Logs del Listener

```bash
sudo docker logs -f chirpstack_listener_app
```

---

## ✅ Test Completo del Flujo

1. Ejecutar el script de entrada en el contenedor:
   ```bash
   sudo docker exec -it chirpstack_listener_app ./entrypoint-dev.sh
   ```

2. En otra terminal, lanzar el test:
   ```bash
   ./mqtt_test.sh
   ```

   Deberías ver algo como:

   ```bash
   🚀 Publicando mensaje MQTT de prueba...
   ⏳ Esperando procesamiento...
   🔎 Consultando base de datos TimescaleDB...
   🛠️ Creando tablas en la base de datos...
   ✅ Tablas creadas correctamente.
    id | device_id |     key     | value |      timestamp      
   ----+-----------+-------------+-------+---------------------
     1 | abcd1234  | temperature |  22.8 | 2025-04-16 04:00:00
     4 | abcd1234  | humidity    |    58 | 2025-04-16 04:00:00
     5 | abcd1234  | humidity    |    58 | 2025-04-16 04:00:00
     3 | abcd1234  | temperature |  22.8 | 2025-04-16 04:00:00
     2 | abcd1234  | temperature |  22.8 | 2025-04-16 04:00:00
   (5 rows)

   🌐 Probando endpoint API...
   ```

---

## 🌐 Consultar API

```bash
curl http://localhost:8999/data/
```

---






## 🚀 Despliegue en Pruebas y Producción

---

### 🧪 Entorno de Pruebas

Usado para testear nuevas funcionalidades, mantener logs visibles y facilitar depuración.

```bash
# Bajar contenedores existentes
sudo docker compose down

# Levantar entorno en modo desarrollo (con logs visibles y reconstrucción completa)
sudo docker compose build --no-cache
sudo docker compose up
```

Opcional: para ejecución en segundo plano:

```bash
sudo docker compose up -d
```

Logs en vivo:

```bash
sudo docker logs -f chirpstack_listener_app
```

Verificación base de datos:

```bash
sudo docker exec -it chirpstack_timescaledb psql -U sensoruser -d sensordata -c "SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;"
```

Ver errores (FastAPI y MQTT):

```bash
sudo docker exec -it chirpstack_listener_app cat /var/log/api.err.log
sudo docker exec -it chirpstack_listener_app cat /var/log/mqtt.err.log
```

---

### 🏭 Entorno de Producción

Recomendaciones para entorno más estable, optimizado y con menor interacción manual.

#### 1. Preparar archivo `.env.production` (si usas variables de entorno)
Incluye variables como:
```
ENV=production
DATABASE_URL=...
MQTT_BROKER=...
```

#### 2. Usar `docker-compose.production.yml` (si tienes uno específico)

```bash
sudo docker compose -f docker-compose.production.yml up -d --build
```

#### 3. Verificar contenedores levantados

```bash
sudo docker ps
```

#### 4. Reiniciar contenedores sin reconstrucción (por cambios en config/env):

```bash
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
```

#### 5. Consultar logs si hay problemas puntuales

```bash
sudo docker logs chirpstack_listener_app
```

---

### 🧼 Limpieza General (Recomendado antes de un despliegue limpio)

```bash
sudo docker stop $(docker ps -q)
sudo docker rm $(docker ps -aq)
sudo docker volume prune -f
sudo docker network prune -f
```




| Qué quieres ver                       | Comando                                                                           |
| ------------------------------------- | --------------------------------------------------------------------------------- |
| STDOUT en tiempo real                 | `docker compose logs -f chirpstack_listener_app`                                  |
| Sólo los últimos 100 registros        | `docker compose logs --tail=100 chirpstack_listener_app`                          |
| Entrar al contenedor y mirar ficheros | `docker exec -it chirpstack_listener_app bash`<br>`tail -f /var/log/mqtt.out.log` |
(el stdout_logfile está definido en supervisord.conf )

