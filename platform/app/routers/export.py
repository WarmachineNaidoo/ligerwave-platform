from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from app.database import supabase, service
from app.middleware.ownership import verify_home_ownership
from app.middleware.auth import get_current_user
from app.services.reports import generate_report
import csv, io, json

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/{home_id}/csv")
async def export_csv(
    home_id: str = Depends(verify_home_ownership),
    event_type: str = Query(None, max_length=50),
    min_confidence: float = Query(None, ge=0, le=1),
    limit: int = Query(1000, ge=1, le=10000),
):
    q = service.table("events").select("*").eq("home_id", home_id).order("timestamp", desc=True).limit(limit)
    if event_type:
        q = q.eq("event_type", event_type)
    if min_confidence is not None:
        q = q.gte("confidence", min_confidence)
    result = q.execute()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["id", "timestamp", "event_type", "confidence", "zone", "resolution", "csi_size_bytes"])
    for e in result.data:
        w.writerow([e["id"], e["timestamp"], e["event_type"], e.get("confidence"), e.get("zone"), e.get("resolution"), e.get("csi_size_bytes")])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=events_{home_id[:8]}.csv"})

@router.get("/{home_id}/json")
async def export_json(
    home_id: str = Depends(verify_home_ownership),
    event_type: str = Query(None, max_length=50),
    min_confidence: float = Query(None, ge=0, le=1),
    limit: int = Query(1000, ge=1, le=10000),
):
    q = service.table("events").select("*").eq("home_id", home_id).order("timestamp", desc=True).limit(limit)
    if event_type:
        q = q.eq("event_type", event_type)
    if min_confidence is not None:
        q = q.gte("confidence", min_confidence)
    result = q.execute()
    return StreamingResponse(iter([json.dumps(result.data, default=str)]), media_type="application/json", headers={"Content-Disposition": f"attachment; filename=events_{home_id[:8]}.json"})

@router.get("/{home_id}/report")
async def export_report(
    home_id: str = Depends(verify_home_ownership),
    months: int = Query(1, ge=1, le=12),
):
    buf = generate_report(home_id, months)
    return StreamingResponse(buf, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename=report_{home_id[:8]}.txt"})
