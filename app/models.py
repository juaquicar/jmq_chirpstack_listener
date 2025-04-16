
from sqlalchemy import Column, String, Float, DateTime, Integer
from app.database import Base
import datetime

class SensorData(Base):
    __tablename__ = "sensor_data"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    key = Column(String, index=True)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
