# README-DEV.md  
Guía completa para levantar la pila **ChirpStack Listener** en LOCAL, desarrollar y depurar sin dolor.

---

## 📋 Requisitos previos

| Herramienta | Versión mínima recomendada |
|-------------|----------------------------|
| **Docker Desktop / engine** | 24.x |
| **Docker Compose** | v2 (integrado) |
| **bash, curl, jq, openssl** | Para scripts de prueba |

> **Nota:** No necesitas Python localmente; se usa la imagen *python:3.12-slim*
dentro del contenedor,e xcepto para probar mqtt_debug.py.

---

## 🗂️ Estructura rápida del repo

| Ruta | ¿Qué contiene?                                                                                                                                                                                  |
|------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `app/` | FastAPI, cliente MQTT, modelos SQLAlchemy & más                                                                                                                                                 |
| `app/ctx/dev/` | Certificados self-signed para desarrollo                                                                                                                                                        |
| `docker-compose.dev.yml` | Orquesta **app + TimescaleDB + Mosquitto** :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}                                                                           |
| `entrypoint-dev.sh` | Arranca Uvicorn con **--reload** :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}                                                                                     |
| `deploy.dev.sh` | Script “todo-en-uno” build + up + logs :contentReference[oaicite:4]{index=4}:contentReference[oaicite:5]{index=5}                                                                               |
| `tests/mqtt_test.sh` | Publica un *uplink* simulado en el mosquitto local lanzado por docker y consulta la API para ver si se ha almacenado :contentReference[oaicite:6]{index=6}:contentReference[oaicite:7]{index=7} |
| `scripts/create_dev_certrts.sh` | Genera certificados auto-firmados (si no existen)                                                                                                                                               |
| `requirements.txt` | Dependencias fijadas para reproducibilidad :contentReference[oaicite:10]{index=10}:contentReference[oaicite:11]{index=11}                                                                       |

### 📂 Listado detallado de `app/`

> Esta carpeta contiene **todo el servicio de backend**: la API (FastAPI), la integración MQTT y la capa de persistencia en TimescaleDB.
> A continuación, una descripción de cada fichero y submódulo habitual dentro de `app/` — ajusta nombres si has cambiado la estructura:

| Ruta (respecto a `app/`)      | ¿Para qué sirve?                                                                                                                            |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `main.py`                     | **Punto de entrada** para Uvicorn – instancia `FastAPI`, registra routers y configura middleware.                                           |
| `database.py`                 | Gestor **SQLAlchemy + asyncpg**: crea el `engine`, sesión (`AsyncSession`) y utilidades de inicialización.                                  |
| `models.py`                   | Modelos ORM de TimescaleDB (tablas de mensajes LoRa, métricas, etc.).                                                                       |
| `mqtt_client.py`              | Cliente **paho-mqtt** (o HBMQTT) con conexión TLS, callbacks `on_message`, reintentos, etc.; reempaqueta payloads a objetos Python.         |
| `schemas.py`                  | Esquemas *pydantic* para request/response de la API y para la cola interna entre MQTT → DB.                                                 |
| `routers/`                    | Subcarpeta con **routers FastAPI** (p. ej. `uplinks.py`, `stats.py`, `health.py`). Cada uno define endpoints REST y depende de `crud/*.py`. |
| `crud/`                       | Funciones de acceso a datos: inserciones en TimescaleDB, consultas agregadas, paginación. Mantiene limpio el código de los routers.         |
| `services/`                   | Lógica de dominio: validaciones, transformaciones, reglas de negocio (por ejemplo, convertir *payloads* binarios a JSON interpretado).      |
| `ctx/`                     | Certificados y claves **self-signed** para entorno local (MQTT y HTTPS).                                                                    |
| `mqtt_debug.py`               | *Sniffer* MQTT de línea de comandos: se conecta al broker, muestra tópicos y payloads crudos para depurar.                                  |


---

## 🚀 Arranque exprés

```bash
git clone https://github.com/juaquicar/jmq_chirpstack_listener.git
cd jmq_chirpstack_listener

cp env.dev.example env.dev          # ajusta variables si quieres (por defecto usa mosquitto interno dockerizado)
bash deploy.dev.sh                  # compila, levanta y sigue logs 🚀
```

* **FastAPI**: [http://localhost:8999/docs](http://localhost:8999/docs)
* **TimescaleDB**: `localhost:15432` (`sensoruser/sensorpass`)
* **Mosquitto**: `localhost:1884` (sin TLS por defecto)

---

## 🔄 Flujo de trabajo

0. Ejecuta el entorno. Lanza un test por si todo esta OK.

```bash
bash deploy.dev.sh
bash test/mqtt_test.sh
```

1. **Edita código** → guarda → Uvicorn recarga automáticamente
   (gracias al volumen `.:/app` en *compose*)&#x20;



2. **Observa logs** en otra terminal:

   ```bash
   docker compose -f docker-compose.dev.yml logs -f app
   ```

3. **Pruebas end-to-end**

   ```bash
   tests/mqtt_test.sh                 # publica JSON + llama API :contentReference[oaicite:14]{index=14}:contentReference[oaicite:15]{index=15}
   ```

4. **Sniffing en tiempo real**

   ```bash
   virtualenv venv
   source venv/bin/activate
   pip3 install -r requirements
   python3 app/mqtt_debug.py           # escucha todos los topics :contentReference[oaicite:16]{index=16}:contentReference[oaicite:17]{index=17}
   ```

---

## 🛠️ Comandos útiles

| Acción                         | Comando                                                                        |
|--------------------------------|--------------------------------------------------------------------------------|
| Abrir **psql** en la base      | `PGPASSWORD=sensorpass psql -h localhost -p 15432 -U sensoruser -d sensordata` |
| Shell dentro del contenedor    | `docker exec -it chirpstack_listener_app bash`                                 |
| Regenerar certs self-signed    | `bash scripts/create_dev_certrts.sh`                                           |
| Reiniciar sólo el servicio app | `docker restart chirpstack_app_dev`                                            |
| Log En Vivo                    | `docker compose -p jmq_chirpstack_listener_dev logs -f app`                    |
| Dockers Activos                | `docker ps`                                                                    |

---

## 🔧 Variables de entorno (env.dev)

| Variable                      | Descripción                                                | Valor por defecto                 |
| ----------------------------- |------------------------------------------------------------| --------------------------------- |
| `ENV`                         | Forzado a `development` por el *compose*                   | `development`                     |
| `DB_HOST/PORT/USER/PASS/NAME` | Conexión TimescaleDB                                       | ver `docker-compose.dev.yml`      |
| `MQTT_BROKER/PORT`            | Broker interno `mosquitto_dev` o externo usar 8883 con TLS | `mosquitto_dev` / `1883`          |
| `MQTT_TOPIC`                  | Wildcard ChirpStack                                        | `application/+/device/+/event/up` |
| `MQTT_CTX_DIR`                | Carpeta de certificados cliente                            | `/app/ctx`                        |
| `HOST` / `PORT`               | Bind de Uvicorn                                            | `0.0.0.0` / `8999`                |

> Cualquier variable en `env.dev` anula la que venga de *compose* por `environment:`.

---

## 🔐 Certificados TLS para mosquitto local (opcional)

1. Ejecuta `scripts/create_dev_certrts.sh` para generar CA, cert y key.
2. Los archivos se guardan en `app/ctx/dev/` y se montan en **mosquitto** y **app** automáticamente. Copialos en mosquitto/config/ctx
3. Activa TLS en Mosquitto editando `mosquitto/config/mosquitto.conf`.

---

## 🧹 Limpieza total

```bash
sudo docker stop $(docker ps -q)
sudo docker rm $(docker ps -aq)
sudo docker volume prune -f
sudo docker network prune -f
```

---


## 🤝 Contribuir

1. Abre una *issue* descriptiva.
2. Crea rama `git checkout -b feat/mi-funcionalidad`.
3. Añade tests en `tests/` y actualiza este README-DEV.md si procede.
4. Envía *pull request* contra `main`.

¡Gracias por mejorar el proyecto! 🚀



