from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

class SensorDataInput(BaseModel):
    zone: str
    device_type: Optional[str] = None

class SensorDataOutput(BaseModel):
    status: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    motion: Optional[bool] = None

class DeviceActionInput(BaseModel):
    device_id: str
    params: Optional[Dict[str, Any]] = None

class DeviceActionOutput(BaseModel):
    status: str
    device_id: str
    action: str

class DimDeviceInput(BaseModel):
    device_id: str
    brightness: float = Field(ge=0, le=1)

class TTSInput(BaseModel):
    text: str
    zone: Optional[str] = None

class TTSOutput(BaseModel):
    status: str
    played_on: List[str]

class AllSensorsInput(BaseModel):
    zone: str

class SensorReading(BaseModel):
    type: str
    value: Any

class AllSensorsOutput(BaseModel):
    status: str
    sensors: List[SensorReading]

class DeviceStatusInput(BaseModel):
    device_id: str

class DeviceStatusOutput(BaseModel):
    status: str
    device_id: str
    state: Dict[str, Any] 