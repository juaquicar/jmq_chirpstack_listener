"""
app/status.py
Estructura global para exponer el estado del cliente MQTT
a la aplicación FastAPI.
"""

import time

mqtt_status = {
    "connected": False,   # bool
    "last_rc": None,      # int  (código de retorno MQTT)
    "last_ts": None,      # float (epoch segundos)
}

def update(connected: bool, rc: int) -> None:
    """
    Actualiza el diccionario de estado.

    connected : True  -> Connected
                False -> Disconnected
    rc        : código devuelto por el broker
    """
    mqtt_status["connected"] = connected
    mqtt_status["last_rc"] = rc
    mqtt_status["last_ts"] = time.time()
