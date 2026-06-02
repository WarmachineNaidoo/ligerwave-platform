from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
from app.database import supabase
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from app.services.simulator import simulators, CsiSimulator
from app.services.storage import upload_csi
from app.services.signal import processors, CsiProcessor
from app.services.arming import arming
from app.services.audit import audit
import binascii

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
    device = supabase.table("devices").select("*").eq("home_id", home_id).execute()
    if device.data:
        raise HTTPException(status_code=409, detail="Home already has a paired device")
    supabase.table("devices").insert({
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
    user = supabase.table("users").select("organization_id").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=403, detail="User not found")
    device = supabase.table("devices").select("home_id,gateway_id").eq("gateway_id", body.gateway_id).execute()
    if not device.data:
        raise HTTPException(status_code=403, detail="Unknown device")
    home_id = device.data[0]["home_id"]
    home = supabase.table("homes").select("organization_id").eq("id", home_id).execute()
    if not home.data or home.data[0]["organization_id"] != user.data[0]["organization_id"]:
        raise HTTPException(status_code=403, detail="Device not linked to your organization")

    processor = processors.get(home_id)
    csi_storage_path = None
    confidence = body.confidence
    event_type = body.event_type

    if body.csi_data_hex and processor:
        try:
            csi_bytes = binascii.unhexlify(body.csi_data_hex)
            result = processor.process_csi(csi_bytes)
            csi_storage_path = upload_csi(str(home_id), csi_bytes)
            if confidence is None:
                confidence = result["confidence"]
            if body.event_type == "unknown" or body.event_type == "normal":
                event_type = result["event_type"]
        except (binascii.Error, ValueError):
            pass

    is_armed = arming.is_armed(home_id)
    should_alert = arming.should_alert(home_id, confidence or 0)

    event = supabase.table("events").insert({
        "home_id": home_id,
        "event_type": event_type,
        "confidence": confidence,
        "zone": body.zone,
        "zone_path": body.zone_path,
        "csi_size_bytes": len(body.csi_data_hex or "") // 2 if body.csi_data_hex else None
    }).execute()

    event_id = event.data[0]["id"]

    if csi_storage_path:
        supabase.table("csi_raw").insert({
            "event_id": event_id,
            "storage_path": csi_storage_path,
            "size_bytes": len(body.csi_data_hex or "") // 2 if body.csi_data_hex else 0
        }).execute()

    if should_alert:
        supabase.table("homes").update({"status": "armed"}).eq("id", home_id).execute()

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
