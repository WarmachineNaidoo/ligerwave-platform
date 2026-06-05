from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional
from app.database import supabase, service
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from app.services.storage import get_csi
import numpy as np, json

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/{home_id}")
async def list_events(
    home_id: str = Depends(verify_home_ownership),
    event_type: Optional[str] = Query(None, max_length=50),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    payload: dict = Depends(get_current_user)
):
    q = service.table("events").select("*").eq("home_id", home_id).order("timestamp", desc=True)
    if event_type:
        q = q.eq("event_type", event_type)
    if min_confidence is not None:
        q = q.gte("confidence", min_confidence)
    result = q.range(offset, offset + limit - 1).execute()
    return {"events": result.data, "total": len(result.data), "offset": offset, "limit": limit}

@router.get("/{home_id}/count")
async def count_events(
    home_id: str = Depends(verify_home_ownership),
    event_type: Optional[str] = Query(None, max_length=50),
    payload: dict = Depends(get_current_user)
):
    q = service.table("events").select("id", count="exact").eq("home_id", home_id)
    if event_type:
        q = q.eq("event_type", event_type)
    result = q.execute()
    return {"total": result.count if hasattr(result, 'count') else 0}

@router.get("/{home_id}/{event_id}")
async def get_event(
    home_id: str = Depends(verify_home_ownership),
    event_id: str = None
):
    result = service.table("events").select("*").eq("id", event_id).eq("home_id", home_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Event not found")
    return result.data[0]

@router.get("/{home_id}/{event_id}/csi")
async def get_event_csi(
    home_id: str = Depends(verify_home_ownership),
    event_id: str = None
):
    result = service.table("events").select("id,csi_size_bytes").eq("id", event_id).eq("home_id", home_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Event not found")
    if not result.data[0].get("csi_size_bytes"):
        return JSONResponse(content={"amplitude": [], "subcarriers": 52, "packets": 0})
    try:
        raw = get_csi(event_id)
        data = np.frombuffer(raw, dtype=np.float32)
        if data.size < 52:
            return JSONResponse(content={"amplitude": [], "subcarriers": 52, "packets": 0})
        # Return amplitude as 2D array [packets][subcarriers]
        n = 52
        packets = data.size // n
        trimmed = data[:packets * n].reshape(packets, n).tolist()
        return JSONResponse(content={"amplitude": trimmed, "subcarriers": n, "packets": packets})
    except Exception:
        return JSONResponse(content={"amplitude": [], "subcarriers": 52, "packets": 0})
