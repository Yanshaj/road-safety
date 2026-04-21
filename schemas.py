from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DetectionEventCreate(BaseModel):
    latitude: float
    longitude: float
    damage_type: str
    severity_score: float
    image_url: Optional[str] = None

class DetectionEventResponse(DetectionEventCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
