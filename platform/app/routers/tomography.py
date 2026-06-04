from fastapi import APIRouter, Depends
from app.database import supabase, service
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from app.services.tomography import TomographyEngine, engines
from datetime import datetime, timezone

router = APIRouter(prefix="/tomography", tags=["tomography"])

def _ensure_engine(home_id: str):
    if home_id not in engines:
        engines[home_id] = TomographyEngine()
    eng = engines[home_id]
    cutoff = datetime.now(timezone.utc)
    events = service.table("events").select("zone,zone_path,confidence,timestamp").eq("home_id", home_id).gte("timestamp", cutoff.isoformat()).order("timestamp", desc=True).limit(200).execute()
    for e in reversed(events.data or []):
        ts = e.get("timestamp")
        if ts:
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except:
                ts = cutoff
        eng.ingest_event(home_id, e.get("zone") or "", e.get("zone_path") or [], e.get("confidence") or 0.0, ts)
    return eng

@router.get("/{home_id}")
async def get_tomography(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    eng = _ensure_engine(home_id)
    return eng.get_snapshot(home_id)
