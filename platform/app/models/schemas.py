from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., max_length=200)
    organization_id: Optional[UUID] = None

class HomeResponse(BaseModel):
    id: UUID
    name: str
    address: str
    tier: str
    status: str
    created_at: datetime

class EventResponse(BaseModel):
    id: UUID
    home_id: UUID
    event_type: str
    confidence: Optional[float]
    zone: Optional[str]
    timestamp: datetime
    resolution: Optional[str]
