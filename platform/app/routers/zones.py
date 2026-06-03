from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from app.database import service
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
import httpx
from app.config import settings

router = APIRouter(prefix="/zones", tags=["zones"])

def _meta(user_id: str):
    h = {"apikey": settings.supabase_service_key, "Authorization": "Bearer " + settings.supabase_service_key}
    r = httpx.get(f"{settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=h)
    return r.json().get("user_metadata", {}) or {} if r.status_code == 200 else {}

def _save_meta(user_id: str, data: dict):
    h = {"apikey": settings.supabase_service_key, "Authorization": "Bearer " + settings.supabase_service_key, "Content-Type": "application/json"}
    httpx.put(f"{settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=h, json={"user_metadata": data})

class ZoneDef(BaseModel):
    name: str = Field(..., max_length=100)
    sensitivity: float = Field(default=0.8, ge=0.1, le=1.0)

class ZoneConfig(BaseModel):
    zones: List[ZoneDef]

@router.get("/{home_id}")
async def get_zones(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = _meta(user_id)
    zones_map = meta.get("zones", {})
    return zones_map.get(home_id, [])

@router.put("/{home_id}")
async def set_zones(body: ZoneConfig, home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = _meta(user_id)
    zones_map = meta.get("zones", {})
    zones_map[home_id] = [z.model_dump() for z in body.zones]
    meta["zones"] = zones_map
    _save_meta(user_id, meta)
    return zones_map[home_id]
