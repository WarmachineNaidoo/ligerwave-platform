from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.database import supabase
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership

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
    q = supabase.table("events").select("*").eq("home_id", home_id).order("timestamp", desc=True)
    if event_type:
        q = q.eq("event_type", event_type)
    if min_confidence is not None:
        q = q.gte("confidence", min_confidence)
    result = q.range(offset, offset + limit - 1).execute()
    return {"events": result.data, "total": len(result.data)}

@router.get("/{home_id}/{event_id}")
async def get_event(
    home_id: str = Depends(verify_home_ownership),
    event_id: str = None
):
    result = supabase.table("events").select("*").eq("id", event_id).eq("home_id", home_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Event not found")
    return result.data[0]
