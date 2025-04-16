
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app import models
from app.schemas import SensorDataCreate, SensorDataResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def read_root():
    return {"status": "running"}

@app.get("/measurements/", response_model=List[SensorDataResponse])
def get_measurements(device_id: str, start: datetime, end: datetime, db: Session = Depends(get_db)):
    return db.query(models.SensorData)        .filter(models.SensorData.device_id == device_id)        .filter(models.SensorData.timestamp.between(start, end))        .all()


@app.get("/latest_measurements/", response_model=List[SensorDataResponse])
def get_latest_measurements(device_id: str, db: Session = Depends(get_db)):
    subquery = (
        db.query(
            models.SensorData.key,
            db.func.max(models.SensorData.timestamp).label("max_timestamp")
        )
        .filter(models.SensorData.device_id == device_id)
        .group_by(models.SensorData.key)
        .subquery()
    )

    query = (
        db.query(models.SensorData)
        .join(subquery, 
              (models.SensorData.key == subquery.c.key) & 
              (models.SensorData.timestamp == subquery.c.max_timestamp))
        .filter(models.SensorData.device_id == device_id)
    )

    return query.all()


from fastapi.responses import JSONResponse
from collections import defaultdict

@app.get("/latest_measurements_grouped/")
def get_latest_measurements_grouped(device_id: str, db: Session = Depends(get_db)):
    subquery = (
        db.query(
            models.SensorData.key,
            db.func.max(models.SensorData.timestamp).label("max_timestamp")
        )
        .filter(models.SensorData.device_id == device_id)
        .group_by(models.SensorData.key)
        .subquery()
    )

    query = (
        db.query(models.SensorData)
        .join(subquery, 
              (models.SensorData.key == subquery.c.key) & 
              (models.SensorData.timestamp == subquery.c.max_timestamp))
        .filter(models.SensorData.device_id == device_id)
    )

    grouped = {}
    for record in query.all():
        grouped[record.key] = {
            "value": record.value,
            "timestamp": record.timestamp.isoformat()
        }

    return JSONResponse(content=grouped)


@app.get("/timeseries/", response_model=List[SensorDataResponse])
def get_timeseries(
    device_id: str, 
    key: str, 
    start: datetime, 
    end: datetime, 
    db: Session = Depends(get_db)
):
    query = (
        db.query(models.SensorData)
        .filter(models.SensorData.device_id == device_id)
        .filter(models.SensorData.key == key)
        .filter(models.SensorData.timestamp.between(start, end))
        .order_by(models.SensorData.timestamp.asc())
    )
    return query.all()


@app.get("/timeseries/aggregated/")
def get_aggregated_timeseries(
    device_id: str,
    key: str,
    start: datetime,
    end: datetime,
    interval: str = "hour",  # Puede ser: hour, day, week
    db: Session = Depends(get_db)
):
    interval_map = {
        "hour": "1 hour",
        "day": "1 day",
        "week": "1 week"
    }
    if interval not in interval_map:
        return {"error": "Invalid interval. Use one of: hour, day, week."}

    sql = f'''
        SELECT 
            time_bucket(%s, timestamp) AS bucket,
            AVG(value) as average
        FROM sensor_data
        WHERE device_id = %s AND key = %s AND timestamp BETWEEN %s AND %s
        GROUP BY bucket
        ORDER BY bucket
    '''
    result = db.execute(sql, (
        interval_map[interval],
        device_id,
        key,
        start,
        end
    ))

    return [{"timestamp": row[0].isoformat(), "average": row[1]} for row in result]


@app.get("/timeseries/aggregated/full/")
def get_full_aggregated_timeseries(
    device_id: str,
    key: str,
    start: datetime,
    end: datetime,
    interval: str = "hour",  # Puede ser: hour, day, week
    db: Session = Depends(get_db)
):
    interval_map = {
        "hour": "1 hour",
        "day": "1 day",
        "week": "1 week"
    }
    if interval not in interval_map:
        return {"error": "Invalid interval. Use one of: hour, day, week."}

    sql = f'''
        SELECT 
            time_bucket(%s, timestamp) AS bucket,
            AVG(value) as average,
            MAX(value) as maximum,
            MIN(value) as minimum
        FROM sensor_data
        WHERE device_id = %s AND key = %s AND timestamp BETWEEN %s AND %s
        GROUP BY bucket
        ORDER BY bucket
    '''
    result = db.execute(sql, (
        interval_map[interval],
        device_id,
        key,
        start,
        end
    ))

    return [
        {
            "timestamp": row[0].isoformat(),
            "average": row[1],
            "maximum": row[2],
            "minimum": row[3]
        }
        for row in result
    ]


from fastapi import Query

@app.get("/timeseries/aggregated/multi/")
def get_multi_sensor_aggregated(
    device_ids: List[str] = Query(...),
    key: str = "",
    start: datetime = None,
    end: datetime = None,
    interval: str = "hour",
    db: Session = Depends(get_db)
):
    interval_map = {
        "hour": "1 hour",
        "day": "1 day",
        "week": "1 week"
    }
    if interval not in interval_map:
        return {"error": "Invalid interval. Use one of: hour, day, week."}

    sql = f'''
        SELECT 
            device_id,
            time_bucket(%s, timestamp) AS bucket,
            AVG(value) as average,
            MAX(value) as maximum,
            MIN(value) as minimum
        FROM sensor_data
        WHERE device_id = ANY(%s) AND key = %s AND timestamp BETWEEN %s AND %s
        GROUP BY device_id, bucket
        ORDER BY device_id, bucket
    '''
    result = db.execute(sql, (
        interval_map[interval],
        device_ids,
        key,
        start,
        end
    ))

    grouped = {}
    for row in result:
        device = row[0]
        if device not in grouped:
            grouped[device] = []
        grouped[device].append({
            "timestamp": row[1].isoformat(),
            "average": row[2],
            "maximum": row[3],
            "minimum": row[4]
        })

    return grouped


@app.get("/data/")
def read_sensor_data(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.SensorData).order_by(models.SensorData.timestamp.desc()).limit(limit).all()



import threading
from app import mqtt_client

def start_mqtt():
    client = mqtt_client.mqtt.Client()
    client.on_connect = mqtt_client.on_connect
    client.on_disconnect = mqtt_client.on_disconnect
    client.on_message = mqtt_client.on_message
    client.connect("mosquitto", 1883, 60)
    client.loop_forever()

mqtt_thread = threading.Thread(target=start_mqtt)
mqtt_thread.start()