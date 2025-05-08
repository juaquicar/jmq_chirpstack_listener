from datetime import datetime
from pydantic import BaseModel

class SensorDataBase(BaseModel):
    device_id: str
    key: str
    value: float
    timestamp: datetime

    model_config = dict(from_attributes=True)  # ← reemplaza a orm_mode

class SensorDataCreate(SensorDataBase):
    pass

class SensorDataResponse(SensorDataBase):
    id: int
