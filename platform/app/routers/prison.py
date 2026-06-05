from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.middleware.auth import get_current_user, require_role
from app.database import service
from app.services.prison import prison_engine
from app.services.log import logger

router = APIRouter(prefix="/prison", tags=["prison"])

def _verify_org_access(payload: dict) -> str:
    user_id = payload.get("sub")
    user = service.table("users").select("organization_id").eq("id", user_id).execute()
    if not user.data or not user.data[0].get("organization_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    return user.data[0]["organization_id"]

def _namespace_key(org_id: str, block_id: str) -> str:
    return f"{org_id}:{block_id}"

class ThresholdUpdate(BaseModel):
    key: str = Field(..., max_length=50)
    value: float = Field(..., ge=0)

class BlockIngest(BaseModel):
    block_id: str = Field(..., max_length=100)
    hr: Optional[float] = Field(None, ge=20, le=250)
    occupancy: Optional[int] = Field(None, ge=0)
    crowded_cells: Optional[int] = Field(None, ge=0)
    pacing_count: Optional[int] = Field(None, ge=0)
    movement_amplitude: Optional[float] = Field(None, ge=0, le=5)

@router.get("/blocks")
async def get_all_blocks(payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload)
    blocks = prison_engine.get_all_status()
    return {"blocks": blocks, "total": len(blocks), "alert_count": sum(1 for b in blocks if b["status"] == "alert")}

@router.get("/blocks/{block_id}")
async def get_block(block_id: str, payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload)
    nskey = _namespace_key(org_id, block_id)
    block = prison_engine.get_block(nskey)
    return block.compute_riot_probability()

@router.post("/blocks/ingest")
async def ingest_block_data(body: BlockIngest, payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload)
    nskey = _namespace_key(org_id, body.block_id)
    block = prison_engine.get_block(nskey)
    if body.hr is not None:
        block.ingest_hr(body.hr)
    if body.occupancy is not None:
        block.ingest_occupancy(body.occupancy, body.crowded_cells or 0, body.pacing_count or 0, body.movement_amplitude or 0.5)
    return {"status": "ingested", "block_id": body.block_id}

@router.post("/blocks/{block_id}/threshold")
async def set_block_threshold(block_id: str, body: ThresholdUpdate, payload: dict = Depends(require_role("admin"))):
    org_id = _verify_org_access(payload)
    nskey = _namespace_key(org_id, block_id)
    block = prison_engine.get_block(nskey)
    block.set_threshold(body.key, body.value)
    logger.info("prison_threshold_updated", extra={"extra": {"block_id": block_id, "key": body.key, "value": body.value, "user_id": payload["sub"]}})
    return {"status": "updated", "block_id": block_id, "key": body.key, "value": body.value}

@router.post("/thresholds/global")
async def set_global_threshold(body: ThresholdUpdate, payload: dict = Depends(require_role("admin"))):
    org_id = _verify_org_access(payload)
    prison_engine.set_global_threshold(body.key, body.value)
    logger.info("prison_threshold_global_updated", extra={"extra": {"key": body.key, "value": body.value, "user_id": payload["sub"]}})
    return {"status": "global_updated", "key": body.key, "value": body.value}

@router.get("/dashboard")
async def get_dashboard(payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload)
    blocks = prison_engine.get_all_status()
    alert_blocks = [b for b in blocks if b["status"] == "alert"]
    return {
        "blocks": [b for b in blocks if b.get("org_id") == org_id],
        "total_blocks": len(blocks),
        "alert_blocks": len(alert_blocks),
        "inmates": sum(b.get("occupancy", 0) for b in blocks),
        "top_alert": alert_blocks[:3] if alert_blocks else [],
    }
