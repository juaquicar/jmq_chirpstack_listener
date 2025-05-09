# Despliegue en Producción - jmq_chirpstack_listener

Este documento describe el procedimiento para desplegar el proyecto en producción.

## Preparativos

0. Mete los certificados MQTT correspondientes en app/ctx/*
1. Configura el archivo `.env.production` con las variables de entorno necesarias.
2. Asegúrate de tener el archivo `docker-compose.production.yml` correcto.
3. Verifica que el Dockerfile está optimizado para producción.

## Despliegue

Usa el script `deploy.production.sh` para automatizar el despliegue:

```bash
  sudo bash deploy.production.sh
```

## Verificación y Monitoreo

- Verifica que los contenedores estén activos:
  ```bash
  docker ps
  ```
- Para ver logs:
  ```bash
  sudo docker logs chirpstack_listener_app
  ```

## Mantenimiento y Rollback

Si ocurre algún problema:
- Detén los contenedores:
  ```bash
  docker compose -f docker-compose.production.yml down
  ```
- Realiza ajustes y vuelve a desplegar con `deploy.production.sh`.


# Nginx Config

`/etc/nginx/sites-enabled/jmq_listener`

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8999;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Luego puedes aplicar LetEncrypt! para habilitar https.

## FAQ

- **Error de conexión a la BD:** Revisa las variables de entorno en `.env.production`.
- **Problemas con MQTT:** Confirma que el broker MQTT esté accesible y que el tópico configurado sea correcto.