from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.database import supabase, service
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from app.services.audit import audit
from datetime import datetime, timezone

router = APIRouter(prefix="/arming", tags=["arming"])

class Schedule(BaseModel):
    monday_start: Optional[str] = Field(None, max_length=5)
    monday_end: Optional[str] = Field(None, max_length=5)
    tuesday_start: Optional[str] = Field(None, max_length=5)
    tuesday_end: Optional[str] = Field(None, max_length=5)
    wednesday_start: Optional[str] = Field(None, max_length=5)
    wednesday_end: Optional[str] = Field(None, max_length=5)
    thursday_start: Optional[str] = Field(None, max_length=5)
    thursday_end: Optional[str] = Field(None, max_length=5)
    friday_start: Optional[str] = Field(None, max_length=5)
    friday_end: Optional[str] = Field(None, max_length=5)
    saturday_start: Optional[str] = Field(None, max_length=5)
    saturday_end: Optional[str] = Field(None, max_length=5)
    sunday_start: Optional[str] = Field(None, max_length=5)
    sunday_end: Optional[str] = Field(None, max_length=5)

@router.post("/schedule")
async def set_schedule(
    body: Schedule,
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user)
):
    data = body.model_dump(exclude_none=True)
    data["home_id"] = home_id
    existing = service.table("arming_schedules").select("*").eq("home_id", home_id).execute()
    if existing.data:
        service.table("arming_schedules").update(data).eq("home_id", home_id).execute()
    else:
        service.table("arming_schedules").insert(data).execute()
    audit.log(payload.get("sub"), "arming_schedule_updated", "home", resource_id=home_id)
    return {"status": "saved"}

@router.get("/schedule")
async def get_schedule(home_id: str = Depends(verify_home_ownership)):
    result = service.table("arming_schedules").select("*").eq("home_id", home_id).execute()
    if not result.data:
        return {"schedule": None}
    return result.data[0]

@router.post("/override")
async def override_arm(
    armed: bool,
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user)
):
    service.table("arming_schedules").update({
        "manual_override": True,
        "manual_armed": armed
    }).eq("home_id", home_id).execute()
    service.table("homes").update({"status": "armed" if armed else "disarmed"}).eq("id", home_id).execute()
    audit.log(payload.get("sub"), "arming_override", "home", resource_id=home_id, details={"armed": armed})
    return {"status": "armed" if armed else "disarmed"}
