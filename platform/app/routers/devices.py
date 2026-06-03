from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
from app.database import supabase, service
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from app.services.simulator import simulators, CsiSimulator
from app.services.storage import upload_csi
from app.services.signal import processors, CsiProcessor
from app.services.ws import manager
from app.services.arming import arming
from app.services.audit import audit
from app.services.cross_validation import get_validator, CrossValidator
from app.services.baseline import baselines, HomeBaseline
from app.services.log import logger
import binascii, numpy as np

router = APIRouter(prefix="/devices", tags=["devices"])

class PairRequest(BaseModel):
    gateway_id: str = Field(..., min_length=1, max_length=100)
    firmware_ver: Optional[str] = Field(None, max_length=50)

@router.post("/pair")
async def pair_device(
    body: PairRequest,
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user)
):
    device = service.table("devices").select("*").eq("home_id", home_id).execute()
    if device.data:
        raise HTTPException(status_code=409, detail="Home already has a paired device")
    service.table("devices").insert({
        "home_id": home_id,
        "gateway_id": body.gateway_id,
        "firmware_ver": body.firmware_ver,
        "last_seen": datetime.now(timezone.utc).isoformat()
    }).execute()
    simulators[home_id] = CsiSimulator(home_id)
    processors[home_id] = CsiProcessor(home_id)
    audit.log(payload.get("sub"), "device_paired", "device", details={"gateway_id": body.gateway_id})
    return {"status": "paired", "gateway_id": body.gateway_id}

class IngestedEvent(BaseModel):
    event_type: str = Field(default="normal", max_length=50)
    gateway_id: str = Field(..., max_length=100)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    zone: Optional[str] = Field(None, max_length=100)
    zone_path: Optional[list[str]] = Field(None, max_length=50)
    csi_data_hex: Optional[str] = Field(None, max_length=2_000_000)

@router.post("/events")
async def ingest_event(body: IngestedEvent, payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    user = service.table("users").select("organization_id").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=403, detail="User not found")
    device = service.table("devices").select("home_id,gateway_id").eq("gateway_id", body.gateway_id).execute()
    if not device.data:
        raise HTTPException(status_code=403, detail="Unknown device")
    home_id = device.data[0]["home_id"]
    home = service.table("homes").select("organization_id").eq("id", home_id).execute()
    if not home.data or home.data[0]["organization_id"] != user.data[0]["organization_id"]:
        raise HTTPException(status_code=403, detail="Device not linked to your organization")

    if home_id not in processors:
        processors[home_id] = CsiProcessor(home_id)
    processor = processors[home_id]
    csi_storage_path = None
    confidence = body.confidence
    event_type = body.event_type

    if body.csi_data_hex:
        try:
            csi_bytes = binascii.unhexlify(body.csi_data_hex)
        except binascii.Error:
            raise HTTPException(status_code=400, detail="Invalid csi_data_hex format")
        result = processor.process_csi(csi_bytes)
        if confidence is None:
            confidence = result["confidence"]
        if body.event_type == "unknown" or body.event_type == "normal":
            event_type = result["event_type"]

    is_armed = arming.is_armed(home_id)
    should_alert = arming.should_alert(home_id, confidence or 0)

    # Cross-validate using sensor fusion (CSI + mmWave + door)
    validator = get_validator(home_id)
    cv = validator.ingest_csi(event_type, confidence or 0.5, body.zone or "default")
    fused_confidence = cv["fused_confidence"]
    should_alert = cv["should_alert"]
    fusion_info = {"sensors": cv["sensors"], "fused_confidence": fused_confidence}
    logger.info("cross_validation", extra={"extra": {"home_id": home_id, **fusion_info, "original_confidence": confidence}})

    event = service.table("events").insert({
        "home_id": home_id,
        "event_type": event_type,
        "confidence": confidence,
        "zone": body.zone,
        "zone_path": body.zone_path,
        "csi_size_bytes": len(body.csi_data_hex or "") // 2 if body.csi_data_hex else None
    }).execute()

    event_id = event.data[0]["id"]

    if body.csi_data_hex:
        csi_bytes = binascii.unhexlify(body.csi_data_hex)
        csi_storage_path = upload_csi(event_id, csi_bytes)
        if csi_storage_path:
            service.table("csi_raw").insert({
                "event_id": event_id,
                "storage_path": csi_storage_path,
                "size_bytes": len(body.csi_data_hex or "") // 2 if body.csi_data_hex else 0
            }).execute()

        data = np.frombuffer(csi_bytes, dtype=np.float32)
        if data.size >= 156:
            amplitude = data[:156].reshape(3, 52)
            # Feed home baseline (silent learning)
            if home_id not in baselines:
                baselines[home_id] = HomeBaseline(home_id)
            baselines[home_id].add_frame(amplitude)
            from app.services.wellness import breathing_detectors, fall_detectors, apnea_detectors, BreathingDetector, FallDetector, ApneaDetector
            if home_id not in breathing_detectors:
                breathing_detectors[home_id] = BreathingDetector(home_id)
            if home_id not in fall_detectors:
                fall_detectors[home_id] = FallDetector(home_id)
            if home_id not in apnea_detectors:
                apnea_detectors[home_id] = ApneaDetector(home_id)
            breathing_detectors[home_id].add_packet(amplitude)
            fall_detectors[home_id].add_packet(amplitude)
            apnea_detectors[home_id].add_envelope_sample(float(np.mean(np.abs(amplitude))))
            # Feed premium detectors
            try:
                from app.services.premium import DoorWindowDetector, VehicleDetector, FireSmokeDetector, BabyCryDetector, RoomOccupancyDetector, WaterLeakDetector, StructuralDetector, HeartRateDetector, GaitDetector
                from app.routers.premium import detectors as prem_dets
                if home_id not in prem_dets:
                    prem_dets[home_id] = {}
                p = prem_dets[home_id]
                for cls_name, cls, key in [
                    ("DoorWindowDetector", DoorWindowDetector, "door_window"),
                    ("VehicleDetector", VehicleDetector, "vehicle"),
                    ("FireSmokeDetector", FireSmokeDetector, "fire_smoke"),
                    ("BabyCryDetector", BabyCryDetector, "baby_cry"),
                    ("RoomOccupancyDetector", RoomOccupancyDetector, "occupancy"),
                    ("WaterLeakDetector", WaterLeakDetector, "water_leak"),
                    ("StructuralDetector", StructuralDetector, "structural"),
                    ("HeartRateDetector", HeartRateDetector, "heart_rate"),
                    ("GaitDetector", GaitDetector, "gait"),
                ]:
                    if key not in p:
                        p[key] = cls(home_id)
                    p[key].add_packet(amplitude)
            except Exception as e:
                logger.warning("premium_detector_init_failed", extra={"extra": {"action": "init_premium_detectors", "error": str(e)}})

    # Suppress alerts during dark mode learning period
    if home_id in baselines and baselines[home_id].is_learning():
        should_alert = False

    if should_alert:
        service.table("homes").update({"status": "armed"}).eq("id", home_id).execute()

    # Broadcast via WebSocket
    try:
        import asyncio
        asyncio.ensure_future(manager.broadcast_home(home_id, {"type": "event", "data": event.data[0]}))
    except Exception as e:
        logger.warning("ws_broadcast_failed", extra={"extra": {"action": "broadcast_event", "error": str(e)}})

    return {
        **event.data[0],
        "armed": is_armed,
        "should_alert": should_alert,
    }

@router.get("/simulate")
async def simulate_event(
    intrusion: bool = False,
    home_id: str = Depends(verify_home_ownership),
):
    sim = simulators.get(home_id)
    if not sim:
        raise HTTPException(status_code=400, detail="No simulator initialized. Pair a device first.")
    pkt = sim.simulate_packet(intrusion=intrusion)
    processor = processors.get(home_id)
    if processor and pkt.get("csi_data_b64"):
        csi_bytes = bytes.fromhex(pkt["csi_data_b64"])
        result = processor.process_csi(csi_bytes)
        pkt["processed_confidence"] = result["confidence"]
        pkt["processed_type"] = result["event_type"]
    return pkt
