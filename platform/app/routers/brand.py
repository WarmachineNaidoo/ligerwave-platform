from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.middleware.auth import get_current_user
from app.database import service
from app.config import settings
from app.services.log import logger
import httpx

router = APIRouter(prefix="/settings", tags=["settings"])

def _org_meta(user_id: str) -> dict:
    h = {"apikey": settings.supabase_service_key, "Authorization": "Bearer " + settings.supabase_service_key}
    r = httpx.get(f"{settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=h)
    return r.json().get("user_metadata", {}) or {} if r.status_code == 200 else {}

def _save_org_meta(user_id: str, meta: dict):
    h = {"apikey": settings.supabase_service_key, "Authorization": "Bearer " + settings.supabase_service_key, "Content-Type": "application/json"}
    httpx.put(f"{settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=h, json={"user_metadata": meta})

class BrandConfig(BaseModel):
    org_name: str = Field(default="", max_length=200)
    primary_color: str = Field(default="#22d3ee", max_length=7)
    logo_url: str = Field(default="", max_length=500)
    favicon_url: str = Field(default="", max_length=500)
    hide_branding: bool = Field(default=False)
    dashboard_title: str = Field(default="Security Dashboard", max_length=200)

@router.get("/brand")
async def get_brand(payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    user = service.table("users").select("organization_id").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")
    org_id = user.data[0].get("organization_id")
    meta = _org_meta(user_id)
    brand = meta.get("brand", {})
    defaults = {
        "org_name": "Ligerwave",
        "primary_color": "#22d3ee",
        "logo_url": "",
        "favicon_url": "",
        "hide_branding": False,
        "dashboard_title": "CSI Security Dashboard",
    }
    return {**defaults, **brand, "org_id": org_id}

@router.put("/brand")
async def set_brand(body: BrandConfig, payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = _org_meta(user_id)
    meta["brand"] = body.model_dump()
    _save_org_meta(user_id, meta)
    logger.info("brand_updated", extra={"extra": {"user_id": user_id, "org_name": body.org_name}})
    return {"status": "updated", "brand": body.model_dump()}

@router.post("/brand/reset")
async def reset_brand(payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = _org_meta(user_id)
    meta.pop("brand", None)
    _save_org_meta(user_id, meta)
    return {"status": "reset", "brand": {}}
