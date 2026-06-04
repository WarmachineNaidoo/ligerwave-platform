from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.middleware.auth import get_current_user
from app.services.mine import mine_engine
from app.services.log import logger

router = APIRouter(prefix="/mine", tags=["mine"])

class HrIngest(BaseModel):
    zone_id: str = Field(..., max_length=100)
    user_id: str = Field(..., max_length=200)
    hr: float = Field(..., ge=20, le=250)

class GaitIngest(BaseModel):
    zone_id: str = Field(..., max_length=100)
    user_id: str = Field(..., max_length=200)
    stride_length: float = Field(..., ge=0.1, le=5)
    speed: float = Field(..., ge=0.1, le=10)

class ConfinedSpaceAction(BaseModel):
    zone_id: str = Field(..., max_length=100)
    user_id: str = Field(..., max_length=200)
    action: str = Field(..., pattern="^(enter|exit)$")

class SeismicEvent(BaseModel):
    zone_id: str = Field(..., max_length=100)
    magnitude: float = Field(..., ge=0, le=10)

class GasAlarm(BaseModel):
    zone_id: str = Field(..., max_length=100)
    gas_type: str = Field(..., max_length=50)
    level: float = Field(..., ge=0)

class ZoneConfig(BaseModel):
    zone_id: str = Field(..., max_length=100)
    name: str = Field(default="", max_length=200)
    temperature: Optional[float] = Field(None, ge=-10, le=80)
    occupancy: Optional[int] = Field(None, ge=0)
    hazard: Optional[bool] = None

@router.post("/ingest/hr")
async def ingest_hr(body: HrIngest, payload: dict = Depends(get_current_user)):
    zone = mine_engine.get_zone(body.zone_id)
    zone.log_hr(body.user_id, body.hr)
    return {"status": "logged"}

@router.post("/ingest/gait")
async def ingest_gait(body: GaitIngest, payload: dict = Depends(get_current_user)):
    zone = mine_engine.get_zone(body.zone_id)
    zone.log_gait(body.user_id, body.stride_length, body.speed)
    return {"status": "logged"}

@router.get("/fatigue/{zone_id}/{user_id}")
async def get_fatigue(zone_id: str, user_id: str, payload: dict = Depends(get_current_user)):
    zone = mine_engine.get_zone(zone_id)
    return zone.fatigue_index(user_id)

@router.get("/heat-stress/{zone_id}/{user_id}")
async def get_heat_stress(zone_id: str, user_id: str, payload: dict = Depends(get_current_user)):
    zone = mine_engine.get_zone(zone_id)
    return zone.heat_stress_risk(user_id)

@router.post("/confined-space")
async def confined_space_action(body: ConfinedSpaceAction, payload: dict = Depends(get_current_user)):
    zone = mine_engine.get_zone(body.zone_id)
    if body.action == "enter":
        zone.enter_confined_space(body.user_id)
        return {"status": "entered", "zone_id": body.zone_id, "worker": body.user_id}
    elif body.action == "exit":
        result = zone.exit_confined_space()
        return result or {"status": "no_active_entry"}
    raise HTTPException(status_code=400, detail="Invalid action")

@router.get("/confined-space/{zone_id}")
async def get_confined_space(zone_id: str, payload: dict = Depends(get_current_user)):
    zone = mine_engine.get_zone(zone_id)
    return zone.confined_space_status() or {"status": "no_active_entry"}

@router.post("/seismic")
async def seismic_event(body: SeismicEvent, payload: dict = Depends(get_current_user)):
    result = mine_engine.handle_seismic_event(body.magnitude, body.zone_id)
    if result["alert"]:
        logger.critical("seismic_event", extra={"extra": result})
    return result

@router.post("/gas-alarm")
async def gas_alarm(body: GasAlarm, payload: dict = Depends(get_current_user)):
    result = mine_engine.handle_gas_alarm(body.gas_type, body.level, body.zone_id)
    if result["evacuate"]:
        logger.critical("gas_alarm", extra={"extra": result})
    return result

@router.post("/zone")
async def configure_zone(body: ZoneConfig, payload: dict = Depends(get_current_user)):
    zone = mine_engine.get_zone(body.zone_id, body.name)
    if body.temperature is not None:
        zone.temp_c = body.temperature
    if body.occupancy is not None:
        zone.occupancy = body.occupancy
    if body.hazard is not None:
        zone.hazard = body.hazard
    return {"status": "configured", "zone_id": body.zone_id}

@router.get("/summary")
async def get_summary(payload: dict = Depends(get_current_user)):
    return mine_engine.get_summary()
