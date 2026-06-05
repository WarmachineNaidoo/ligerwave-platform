from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.middleware.auth import get_current_user
from app.database import service
from app.services.construction import sites, ConstructionSite
from app.services.log import logger

router = APIRouter(prefix="/construction", tags=["construction"])

def _verify_org_access(payload: dict) -> str:
    user_id = payload.get("sub")
    user = service.table("users").select("organization_id").eq("id", user_id).execute()
    if not user.data or not user.data[0].get("organization_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    return user.data[0]["organization_id"]

def _ns(org_id: str, site_id: str) -> str:
    return f"{org_id}:{site_id}"

class FallDetect(BaseModel):
    site_id: str = Field(..., max_length=100)
    zone_id: str = Field(..., max_length=100)
    vertical_movement: float = Field(..., ge=0, le=20)
    hr: Optional[float] = Field(None, ge=0, le=250)

class CraneCheck(BaseModel):
    site_id: str = Field(..., max_length=100)
    crane_id: str = Field(..., max_length=100)
    person_distance: float = Field(..., ge=0, le=100)
    person_angle: int = Field(..., ge=-180, le=180)

class TrenchCheck(BaseModel):
    site_id: str = Field(..., max_length=100)
    zone_id: str = Field(..., max_length=100)
    vibration: float = Field(..., ge=0, le=5)
    occupancy: int = Field(default=0, ge=0)

class ManOverboardDetect(BaseModel):
    site_id: str = Field(..., max_length=100)
    zone_id: str = Field(..., max_length=100)
    person_present: bool = True
    rail_proximity: float = Field(default=0, ge=0, le=1)

class ZoneConfig(BaseModel):
    site_id: str = Field(..., max_length=100)
    zone_id: str = Field(..., max_length=100)
    name: str = Field(default="", max_length=200)

@router.post("/fall")
async def detect_fall(body: FallDetect, payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload)
    nskey = _ns(org_id, body.site_id)
    if nskey not in sites:
        sites[nskey] = ConstructionSite(body.site_id, body.site_id)
    result = sites[nskey].detect_fall(body.zone_id, body.vertical_movement, body.hr)
    if result and result["severity"] in ("critical", "high"):
        logger.critical("fall_detected", extra={"extra": result})
    return result or {"status": "no_fall_detected"}

@router.post("/crane")
async def check_crane(body: CraneCheck, payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload)
    nskey = _ns(org_id, body.site_id)
    if nskey not in sites:
        sites[nskey] = ConstructionSite(body.site_id, body.site_id)
    result = sites[nskey].check_crane_blind_spot(body.crane_id, body.person_distance, body.person_angle)
    if result["danger"]:
        logger.warning("crane_blind_spot", extra={"extra": result})
    return result

@router.post("/trench")
async def check_trench(body: TrenchCheck, payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload)
    nskey = _ns(org_id, body.site_id)
    if nskey not in sites:
        sites[nskey] = ConstructionSite(body.site_id, body.site_id)
    result = sites[nskey].check_trench(body.zone_id, body.vibration, body.occupancy)
    if result["collapse_risk"]:
        logger.critical("trench_collapse_risk", extra={"extra": result})
    return result

@router.post("/man-overboard")
async def detect_man_overboard(body: ManOverboardDetect, payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload)
    nskey = _ns(org_id, body.site_id)
    if nskey not in sites:
        sites[nskey] = ConstructionSite(body.site_id, body.site_id)
    result = sites[nskey].detect_man_overboard(body.zone_id, body.person_present, body.rail_proximity)
    if result:
        logger.critical("man_overboard", extra={"extra": result})
    return result or {"status": "normal"}

@router.get("/summary/{site_id}")
async def get_summary(site_id: str, payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload)
    nskey = _ns(org_id, site_id)
    if nskey not in sites:
        sites[nskey] = ConstructionSite(site_id, site_id)
    return sites[nskey].get_summary()
