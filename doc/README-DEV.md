
# ChirpStack Listener – Entorno de Desarrollo

Este README describe los pasos para levantar tu entorno de **desarrollo**, consumiendo el mismo broker TLS y TimescaleDB en Docker.

---

## Prerrequisitos

- Docker ≥ 20.10 y Docker Compose ≥ 1.29  
- Clonar este repositorio y posicionarse en su raíz.

## Configuración de variables

1. Copia el `env.dev` de ejemplo:
   ```bash
   cp .env.dev.example .env.dev```
   


2. Rellena los valores según tu entorno (usuario, contraseña, nombres de BD…).

## Certificados TLS

1. Sitúa tus ficheros `ca.crt`, `cert.crt` y `cert.key` en `app/ctx/`.
2. Copia o vincula (`ln -s`) esos ficheros a `mosquitto/config/ctx/` para que el broker los use.

## Arrancar el entorno

```bash
# Construye y levanta todos los servicios en segundo plano
./deploy.dev.sh
```

> Este script hace un `docker compose -f docker-compose.dev.yml down && build && up -d` y luego invoca `entrypoint-dev.sh` .

## Verificación

* **Broker MQTT**

  * TLS: `mosquitto_sub -h localhost -p 8883 --capath /path/to/ca.pem -t '#'`
  * No-TLS: `mosquitto_sub -h localhost -p 1884 -t '#'`

* **TimescaleDB**

  ```bash
  psql -h localhost -p 55432 -U sensoruser -d sensordata -c "\dt"
  ```

* **API FastAPI**
  URL: [`http://localhost:8999`](http://localhost:8999)
  Endpoints:

  * `/health`
  * `/mqtt_status`
  * `/data/?limit=10`
  * … y resto de la doc automática en `/docs`.

## Desarrollo y hot-reload

* El contenedor de la app usa `uvicorn --reload` para que los cambios en `app/` se recarguen automáticamente .
* Para pruebas de integración con MQTT, usa el script `mqtt_test.sh` y ajusta el puerto (1884 o 8883 según quieras TLS) .

---

Con esto ya tienes un **procedimiento reproducible** para desarrollar contra el broker TLS y versus TimescaleDB en Docker, con el mismo juego de certificados de producción. ¡A codificar! 😊

```

### Resumen de cambios principales

- **`env.dev`**: variables de MQTT y DB en desarrollo.  
- **`docker-compose.dev.yml`**: añade el servicio `chirpstack_listener_app` y mapea certificados para TLS.  
- **`README-DEV.md`**: guía paso a paso para levantar, probar y desarrollar.  

Con estos tres artefactos tendrás tu sandbox de desarrollo idéntico a producción, pero con hot-reload y tu propia BD local TimescaleDB montada en Docker. ¡A por ello!
```
