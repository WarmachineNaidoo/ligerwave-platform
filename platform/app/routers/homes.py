from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.database import supabase
from app.middleware.auth import get_current_user, require_role
from app.middleware.ownership import verify_home_ownership
from app.services.audit import audit
from uuid import UUID

router = APIRouter(prefix="/homes", tags=["homes"])

class HomeCreate(BaseModel):
    name: str = Field(..., max_length=200)
    address: str = Field(..., max_length=500)
    lat: Optional[float] = None
    lng: Optional[float] = None

@router.post("")
async def create_home(body: HomeCreate, payload: dict = Depends(require_role("admin", "staff"))):
    org_id = payload.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    result = supabase.table("homes").insert({
        "organization_id": org_id,
        "name": body.name,
        "address": body.address,
        "lat": body.lat,
        "lng": body.lng
    }).execute()
    return result.data[0]

@router.get("")
async def list_homes(payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    user = supabase.table("users").select("organization_id").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=403, detail="User not found")
    org_id = user.data[0].get("organization_id")
    if not org_id:
        return []
    result = supabase.table("homes").select("*").eq("organization_id", org_id).execute()
    return result.data

@router.get("/{home_id}")
async def get_home(home_id: str = Depends(verify_home_ownership)):
    result = supabase.table("homes").select("*").eq("id", home_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Home not found")
    return result.data[0]
