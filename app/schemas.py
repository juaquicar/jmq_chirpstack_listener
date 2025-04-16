
from pydantic import BaseModel
from datetime import datetime

class SensorDataCreate(BaseModel):
    device_id: str
    key: str
    value: float
    timestamp: datetime

class SensorDataResponse(SensorDataCreate):
    id: int

    class Config:
        orm_mode = True
