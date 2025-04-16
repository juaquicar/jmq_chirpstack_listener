# Desarrollo - jmq_chirpstack_listener

Este documento describe el flujo de trabajo para desarrollar en el entorno de jmq_chirpstack_listener.

## Índice
- [Inicio Rápido](#inicio-rápido)
- [Flujo de Trabajo](#flujo-de-trabajo)
- [Pruebas](#pruebas)
- [Limpieza de Contenedores](#limpieza-de-contenedores)
  
## Inicio Rápido

Para levantar el entorno de desarrollo:

```bash
sudo docker compose down --volumes
sudo docker compose build --no-cache
sudo docker compose up
```

O levantarlo en segundo plano:

```bash
sudo docker compose up -d
```

## Flujo de Trabajo de Desarrollo

1. **Levantar el entorno**  
   Usa los comandos anteriores para asegurarte de tener un entorno limpio.

2. **Desarrollar nuevas funcionalidades**  
   Modifica el código según tus necesidades. Si modificas dependencias o el `entrypoint`, recuerda reconstruir la imagen usando `--no-cache`.

3. **Pruebas Funcionales**  
   - Publicar un mensaje MQTT de prueba:
     ```bash
     ./mqtt_test.sh
     ```
   - Verificar datos en la base de datos:
     ```bash
     sudo docker exec -it chirpstack_timescaledb psql -U sensoruser -d sensordata -c "SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;"
     ```
   - Consultar el API:
     ```bash
     curl http://localhost:8999/data/
     ```
   - Revisar logs y errores:
     ```bash
     sudo docker logs -f chirpstack_listener_app
     sudo docker exec -it chirpstack_listener_app cat /var/log/api.err.log
     sudo docker exec -it chirpstack_listener_app cat /var/log/mqtt.err.log
     ```

4. **Iteración y Commit**  
   Realiza commits frecuentes conforme avanzas:
   ```bash
   git add .
   git commit -m "feat: nueva funcionalidad"
   ```

5. **Limpieza**  
   Para limpiar contenedores, volúmenes y redes:
   ```bash
sudo bash -c 'docker stop $(docker ps -a -q)'
sudo bash -c 'sudo docker rm $(docker ps -aq)'
sudo docker volume prune -f
sudo docker network prune -f
   ```