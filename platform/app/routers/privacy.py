from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.middleware.auth import get_current_user
from app.database import service
from app.services.storage import delete_csi
from app.services.log import logger
from datetime import datetime, timezone

router = APIRouter(prefix="/privacy", tags=["privacy"])

@router.get("/my-data")
async def get_my_data(payload: dict = Depends(get_current_user)):
    user_id = payload["sub"]
    user = service.table("users").select("*").eq("id", user_id).execute()
    homes = service.table("homes").select("*").eq("organization_id",
        service.table("users").select("organization_id").eq("id", user_id).execute().data[0]["organization_id"] if service.table("users").select("organization_id").eq("id", user_id).execute().data else None
    ).execute()
    home_ids = [h["id"] for h in homes.data or []]
    events = service.table("events").select("*").in_("home_id", home_ids).order("timestamp", desc=True).limit(1000).execute() if home_ids else {"data": []}
    subscriptions = service.table("subscriptions").select("*").in_("home_id", home_ids).execute() if home_ids else {"data": []}
    api_keys = service.table("api_keys").select("*").in_("home_id", home_ids).execute() if home_ids else {"data": []}
    audit = service.table("audit_logs").select("*").eq("user_id", user_id).order("timestamp", desc=True).limit(500).execute()
    return {
        "user": user.data[0] if user.data else None,
        "homes": homes.data or [],
        "events_count": len(events.data or []),
        "subscriptions": subscriptions.data or [],
        "api_keys": api_keys.data or [],
        "audit_logs": audit.data or [],
        "requested_at": datetime.now(timezone.utc).isoformat()
    }

@router.delete("/my-data")
async def delete_my_data(payload: dict = Depends(get_current_user)):
    user_id = payload["sub"]
    user = service.table("users").select("organization_id").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")
    org_id = user.data[0].get("organization_id")
    if org_id:
        homes = service.table("homes").select("id").eq("organization_id", org_id).execute()
        for home in homes.data or []:
            events = service.table("events").select("id").eq("home_id", home["id"]).execute()
            for event in events.data or []:
                delete_csi(event["id"])
            service.table("events").delete().eq("home_id", home["id"]).execute()
            service.table("csi_raw").delete().eq("home_id", home["id"]).execute()
            service.table("api_keys").delete().eq("home_id", home["id"]).execute()
            service.table("subscriptions").delete().eq("home_id", home["id"]).execute()
            service.table("arming_schedules").delete().eq("home_id", home["id"]).execute()
            service.table("webhooks").delete().eq("home_id", home["id"]).execute()
        service.table("homes").delete().eq("organization_id", org_id).execute()
    service.table("users").update({
        "email": None, "phone": None, "name": None,
        "avatar_url": None, "whatsapp_id": None
    }).eq("id", user_id).execute()
    logger.info("data_subject_deletion", extra={"extra": {"user_id": user_id, "action": "delete_my_data"}})
    return {"status": "deleted", "message": "Personal data deleted. Billing records retained for legal requirements."}

class CorrectionRequest(BaseModel):
    field: str = Field(..., max_length=50)
    value: str = Field(..., max_length=500)

@router.post("/my-data/correction")
async def correct_my_data(body: CorrectionRequest, payload: dict = Depends(get_current_user)):
    user_id = payload["sub"]
    allowed_fields = {"email", "phone", "name"}
    if body.field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"Field must be one of: {', '.join(allowed_fields)}")
    service.table("users").update({body.field: body.value}).eq("id", user_id).execute()
    logger.info("data_subject_correction", extra={"extra": {"user_id": user_id, "field": body.field, "action": "correct_my_data"}})
    return {"status": "corrected", "field": body.field}
