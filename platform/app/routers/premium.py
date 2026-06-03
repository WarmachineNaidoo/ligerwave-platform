from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from app.database import service
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from app.services.features import FEATURES, TIERS, get_subscribed_features, has_feature, set_tier, toggle_feature
from app.services.feature_flags import is_available, get_available_features
from app.services.premium import (
    DoorWindowDetector, VehicleDetector, FireSmokeDetector,
    HeartRateDetector, GaitDetector, RoutineDeviationDetector,
    BabyCryDetector, RoomOccupancyDetector, SmartTriggers,
    WaterLeakDetector, StructuralDetector,
)

router = APIRouter(prefix="/premium", tags=["premium"])

# In-memory detector instances (per home)
detectors: dict = {}

def _get_or_init(home_id: str, cls, key: str):
    if home_id not in detectors:
        detectors[home_id] = {}
    if key not in detectors[home_id]:
        detectors[home_id][key] = cls(home_id)
    return detectors[home_id][key]


class TriggerConfig(BaseModel):
    name: str = Field(..., max_length=50)
    on_event: str = Field(..., max_length=30)
    min_confidence: float = Field(0.5, ge=0, le=1)
    action: str = Field(..., max_length=100)


class GaitLearnRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=50)


# --- Subscription management ---

@router.get("/subscription")
async def get_subscription(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    home = service.table("homes").select("tier,enabled_features").eq("id", home_id).execute()
    if not home.data:
        raise HTTPException(status_code=404)
    row = home.data[0]
    tier = row.get("tier", "free")
    enabled = row.get("enabled_features") or []
    features = []
    for fkey, f in FEATURES.items():
        features.append({
            "key": fkey,
            "tier": f["tier"],
            "price": f["price"],
            "label": f["label"],
            "desc": f["desc"],
            "enabled": fkey in get_subscribed_features(home_id)
        })
    return {"tier": tier, "tier_info": TIERS.get(tier, TIERS["free"]), "features": features}

@router.post("/subscription/tier")
async def update_tier(tier: str, home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    return set_tier(home_id, tier)

@router.post("/subscription/feature")
async def toggle_premium_feature(feature_key: str, enable: bool, home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    return toggle_feature(home_id, feature_key, enable)


# --- Feature endpoints (each requires has_feature check) ---

def _check(home_id: str, feature: str, user_id: str):
    if not is_available(feature, user_id):
        raise HTTPException(status_code=403, detail=f"feature_not_available:{feature}")
    if not has_feature(home_id, feature):
        raise HTTPException(status_code=402, detail=f"feature_not_subscribed:{feature}")

def _uid(payload: dict) -> str:
    return payload.get("sub") or ""


@router.get("/available-features")
async def available_features(payload: dict = Depends(get_current_user)):
    uid = _uid(payload)
    return {"features": get_available_features(uid)}

@router.get("/door-window")
async def get_door_window(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "door_window", _uid(payload))
    d = _get_or_init(home_id, DoorWindowDetector, "door_window")
    return d.get_status()

@router.get("/vehicle")
async def get_vehicle(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "vehicle", _uid(payload))
    d = _get_or_init(home_id, VehicleDetector, "vehicle")
    return d.get_status()

@router.get("/fire-smoke")
async def get_fire_smoke(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "fire_smoke", _uid(payload))
    d = _get_or_init(home_id, FireSmokeDetector, "fire_smoke")
    return d.get_status()

@router.get("/heart-rate")
async def get_heart_rate(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "heart_rate", _uid(payload))
    d = _get_or_init(home_id, HeartRateDetector, "heart_rate")
    return d.detect()

@router.get("/gait")
async def get_gait(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "gait_id", _uid(payload))
    d = _get_or_init(home_id, GaitDetector, "gait")
    return d.detect()

@router.post("/gait/learn")
async def learn_gait(body: GaitLearnRequest, home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "gait_id", _uid(payload))
    d = _get_or_init(home_id, GaitDetector, "gait")
    return d.learn(body.label)

@router.get("/routine-deviation")
async def get_routine_deviation(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "routine_dev", _uid(payload))
    d = _get_or_init(home_id, RoutineDeviationDetector, "routine")
    return d.check()

@router.get("/baby-cry")
async def get_baby_cry(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "baby_cry", _uid(payload))
    d = _get_or_init(home_id, BabyCryDetector, "baby_cry")
    return d.get_status()

@router.get("/room-occupancy")
async def get_room_occupancy(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "room_occupancy", _uid(payload))
    d = _get_or_init(home_id, RoomOccupancyDetector, "occupancy")
    return d.estimate()

@router.get("/smart-triggers")
async def get_smart_triggers(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "smart_triggers", _uid(payload))
    d = _get_or_init(home_id, SmartTriggers, "triggers")
    return d.get_status()

@router.post("/smart-triggers")
async def add_smart_trigger(body: TriggerConfig, home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "smart_triggers", _uid(payload))
    d = _get_or_init(home_id, SmartTriggers, "triggers")
    d.set_trigger(body.model_dump())
    return {"status": "ok", "trigger": body.name}

@router.get("/water-leak")
async def get_water_leak(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "water_leak", _uid(payload))
    d = _get_or_init(home_id, WaterLeakDetector, "water_leak")
    return d.get_status()

@router.get("/structural")
async def get_structural(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    _check(home_id, "structural", _uid(payload))
    d = _get_or_init(home_id, StructuralDetector, "structural")
    return d.check()
