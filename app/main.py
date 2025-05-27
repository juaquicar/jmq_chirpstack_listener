from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app import models
from app.database import Base, engine, get_db
from app.schemas import SensorDataResponse
from app.status import mqtt_status

# --------------------------------------------------------------------------- #
#  Preparación de la base de datos
# --------------------------------------------------------------------------- #

Base.metadata.create_all(bind=engine)

# --------------------------------------------------------------------------- #
#  FastAPI
# --------------------------------------------------------------------------- #

app = FastAPI(title="ChirpStack Listener API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
#  Endpoints básicos
# --------------------------------------------------------------------------- #


@app.get("/health")
def health():
    """Comprueba que el servicio FastAPI está vivo."""
    return {"status": "running"}


@app.get("/mqtt_status")
def mqtt_state():
    """
    Devuelve el estado del cliente MQTT.
    connected : bool
    last_rc   : int  (código devol. por el broker)
    last_ts   : float (epoch segundos)
    """
    return mqtt_status


# --------------------------------------------------------------------------- #
#  Endpoints de mediciones simples
# --------------------------------------------------------------------------- #


@app.get("/data/", response_model=List[SensorDataResponse])
def read_sensor_data(limit: int = 100, db: Session = Depends(get_db)):
    """Devuelve las N últimas filas de sensor_data."""
    return (
        db.query(models.SensorData)
        .order_by(models.SensorData.timestamp.desc())
        .limit(limit)
        .all()
    )


@app.get("/measurements/", response_model=List[SensorDataResponse])
def get_measurements(
    device_id: str,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    """Filtra mediciones de un dispositivo entre dos fechas."""
    return (
        db.query(models.SensorData)
        .filter(models.SensorData.device_id == device_id)
        .filter(models.SensorData.timestamp.between(start, end))
        .all()
    )


@app.get("/latest_measurements/", response_model=List[SensorDataResponse])
def get_latest_measurements(device_id: str, db: Session = Depends(get_db)):
    """Último valor de cada ‘key’ de un dispositivo."""
    subq = (
        db.query(
            models.SensorData.key,
            func.max(models.SensorData.timestamp).label("max_ts"),
        )
        .filter(models.SensorData.device_id == device_id)
        .group_by(models.SensorData.key)
        .subquery()
    )

    return (
        db.query(models.SensorData)
        .join(
            subq,
            (models.SensorData.key == subq.c.key)
            & (models.SensorData.timestamp == subq.c.max_ts),
        )
        .filter(models.SensorData.device_id == device_id)
        .all()
    )


@app.get("/latest_measurements_grouped/")
def get_latest_measurements_grouped(device_id: str, db: Session = Depends(get_db)):
    """Último valor de cada ‘key’, agrupado por clave en el JSON."""
    subq = (
        db.query(
            models.SensorData.key,
            func.max(models.SensorData.timestamp).label("max_ts"),
        )
        .filter(models.SensorData.device_id == device_id)
        .group_by(models.SensorData.key)
        .subquery()
    )

    rows = (
        db.query(models.SensorData)
        .join(
            subq,
            (models.SensorData.key == subq.c.key)
            & (models.SensorData.timestamp == subq.c.max_ts),
        )
        .filter(models.SensorData.device_id == device_id)
        .all()
    )

    return JSONResponse(
        content={
            r.key: {"value": r.value, "timestamp": r.timestamp.isoformat()}
            for r in rows
        }
    )


@app.get("/timeseries/", response_model=List[SensorDataResponse])
def get_timeseries(
    device_id: str,
    key: str,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    """Serie temporal cruda de un sensor (sin agregación)."""
    return (
        db.query(models.SensorData)
        .filter(
            models.SensorData.device_id == device_id,
            models.SensorData.key == key,
            models.SensorData.timestamp.between(start, end),
        )
        .order_by(models.SensorData.timestamp.asc())
        .all()
    )

# --------------------------------------------------------------------------- #
#  Agregaciones con time-bucket (TimescaleDB)
# --------------------------------------------------------------------------- #

_INTERVALS = {"hour": "1 hour", "day": "1 day", "week": "1 week"}


@app.get("/timeseries/aggregated/")
def get_aggregated_timeseries(
    device_id: str,
    key: str,
    start: datetime,
    end: datetime,
    interval: str = "hour",
    db: Session = Depends(get_db),
):
    """Media por intervalo (hour/day/week)."""
    if interval not in _INTERVALS:
        return {"error": "Invalid interval. Use one of: hour, day, week."}

    sql = text("""
        SELECT 
            time_bucket(:interval, timestamp) AS bucket,
            AVG(value) AS average
        FROM sensor_data
        WHERE device_id = :device_id AND key = :key AND timestamp BETWEEN :start AND :end
        GROUP BY bucket
        ORDER BY bucket
    """)
    result = db.execute(
        sql,
        {
            "interval": _INTERVALS[interval],
            "device_id": device_id,
            "key": key,
            "start": start,
            "end": end,
        }
    )
    return [
        {"timestamp": row[0].isoformat(), "average": row[1]} for row in result
    ]

@app.get("/timeseries/aggregated/full/")
def get_full_aggregated_timeseries(
    device_id: str,
    key: str,
    start: datetime,
    end: datetime,
    interval: str = "hour",
    db: Session = Depends(get_db),
):
    """Media, máximo y mínimo por intervalo."""
    if interval not in _INTERVALS:
        return {"error": "Invalid interval. Use one of: hour, day, week."}

    sql = text("""
        SELECT 
            time_bucket(:interval, timestamp) AS bucket,
            AVG(value) AS average,
            MAX(value) AS maximum,
            MIN(value) AS minimum
        FROM sensor_data
        WHERE device_id = :device_id AND key = :key AND timestamp BETWEEN :start AND :end
        GROUP BY bucket
        ORDER BY bucket
    """)
    result = db.execute(
        sql,
        {
            "interval": _INTERVALS[interval],
            "device_id": device_id,
            "key": key,
            "start": start,
            "end": end,
        }
    )
    return [
        {
            "timestamp": row[0].isoformat(),
            "average": row[1],
            "maximum": row[2],
            "minimum": row[3],
        }
        for row in result
    ]


@app.get("/timeseries/aggregated/multi/")
def get_multi_sensor_aggregated(
    device_ids: List[str] = Query(...),
    key: str = "",
    start: datetime = None,
    end: datetime = None,
    interval: str = "hour",
    db: Session = Depends(get_db),
):
    if interval not in _INTERVALS:
        return {"error": "Invalid interval. Use one of: hour, day, week."}

    sql = text("""
        SELECT 
            device_id,
            time_bucket(:interval, timestamp) AS bucket,
            AVG(value) AS average,
            MAX(value) AS maximum,
            MIN(value) AS minimum
        FROM sensor_data
        WHERE device_id = ANY(:device_ids) AND key = :key AND timestamp BETWEEN :start AND :end
        GROUP BY device_id, bucket
        ORDER BY device_id, bucket
    """)

    result = db.execute(
        sql,
        {
            "interval": _INTERVALS[interval],
            "device_ids": device_ids,
            "key": key,
            "start": start,
            "end": end,
        }
    )

    grouped = {}
    for row in result:
        device = row[0]
        grouped.setdefault(device, []).append(
            {
                "timestamp": row[1].isoformat(),
                "average": row[2],
                "maximum": row[3],
                "minimum": row[4],
            }
        )
    return grouped

@app.get("/latest_measurements_all/", response_model=List[SensorDataResponse])
def get_latest_measurements_all(db: Session = Depends(get_db)):
    """
    Último valor de cada (device_id, key) en toda la tabla.
    """
    subq = (
        db.query(
            models.SensorData.device_id,
            models.SensorData.key,
            func.max(models.SensorData.timestamp).label("max_ts"),
        )
        .group_by(models.SensorData.device_id, models.SensorData.key)
        .subquery()
    )

    return (
        db.query(models.SensorData)
        .join(
            subq,
            (models.SensorData.device_id == subq.c.device_id)
            & (models.SensorData.key == subq.c.key)
            & (models.SensorData.timestamp == subq.c.max_ts),
        )
        .all()
    )


@app.get("/latest_measurements_all_grouped/")
def get_latest_measurements_all_grouped(db: Session = Depends(get_db)):
    """
    Último valor de cada key, agrupado por device_id.
    """
    subq = (
        db.query(
            models.SensorData.device_id,
            models.SensorData.key,
            func.max(models.SensorData.timestamp).label("max_ts"),
        )
        .group_by(models.SensorData.device_id, models.SensorData.key)
        .subquery()
    )

    rows = (
        db.query(models.SensorData)
        .join(
            subq,
            (models.SensorData.device_id == subq.c.device_id)
            & (models.SensorData.key == subq.c.key)
            & (models.SensorData.timestamp == subq.c.max_ts),
        )
        .all()
    )

    # Construimos un dict de la forma { device_id: { key: { value, timestamp } } }
    result = {}
    for r in rows:
        result.setdefault(r.device_id, {})[r.key] = {
            "value": r.value,
            "timestamp": r.timestamp.isoformat(),
        }

    return JSONResponse(content=result)





# --------------------------------------------------------------------------- #
#  Lanzar el cliente MQTT en un hilo “daemon”
# --------------------------------------------------------------------------- #

import threading
from app.mqtt_client import run as mqtt_run

mqtt_thread = threading.Thread(target=mqtt_run, daemon=True)
mqtt_thread.start()
