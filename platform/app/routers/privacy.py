from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional
from app.middleware.auth import get_current_user
from app.database import service
from app.services.storage import delete_csi
from app.services.log import logger
from app.config import settings
from datetime import datetime, timezone

router = APIRouter(prefix="/privacy", tags=["privacy"])

# ─── 1. Consent Records ────────────────────────────────────────────

class ConsentRecord(BaseModel):
    consent_type: str = Field(..., max_length=100)
    consented: bool = True
    consent_version: str = Field(default="1.0", max_length=20)

@router.post("/consent")
async def record_consent(body: ConsentRecord, request: Request, payload: dict = Depends(get_current_user)):
    user_id = payload["sub"]
    record = {
        "user_id": user_id,
        "action": "consent",
        "resource_type": "consent",
        "resource_id": body.consent_type,
        "details": {
            "consent_type": body.consent_type,
            "consented": body.consented,
            "consent_version": body.consent_version,
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "ip_address": request.client.host if request.client else "unknown",
    }
    service.table("audit_logs").insert(record).execute()
    logger.info("consent_recorded", extra={"extra": {
        "user_id": user_id, "consent_type": body.consent_type,
        "consented": body.consented, "version": body.consent_version
    }})
    return {"status": "recorded", "consent_type": body.consent_type, "consented": body.consented}

# ─── 2. Data Portability ────────────────────────────────────────────

@router.get("/my-data/export")
async def export_my_data(format: str = Query("json", regex="^(json|csv)$"), payload: dict = Depends(get_current_user)):
    user_id = payload["sub"]
    user = service.table("users").select("email,name,created_at").eq("id", user_id).execute()
    homes = service.table("homes").select("id,name,address,status,created_at").eq("organization_id",
        service.table("users").select("organization_id").eq("id", user_id).execute().data[0]["organization_id"]
    ).execute() if user.data else {"data": []}
    home_ids = [h["id"] for h in homes.data or []]
    events = service.table("events").select("event_type,confidence,zone,zone_path,timestamp").in_("home_id", home_ids).order("timestamp", desc=True).limit(5000).execute() if home_ids else {"data": []}
    subscriptions = service.table("subscriptions").select("tier,status,amount_cents,currency,current_period_start,current_period_end").in_("home_id", home_ids).execute() if home_ids else {"data": []}
    api_keys = service.table("api_keys").select("label,permissions,expires_at,created_at").in_("home_id", home_ids).execute() if home_ids else {"data": []}
    data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": user.data[0] if user.data else None,
        "homes": homes.data or [],
        "events": events.data or [],
        "subscriptions": subscriptions.data or [],
        "api_keys": api_keys.data or [],
    }
    if format == "csv":
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["section", "field", "value"])
        for s, items in data.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            writer.writerow([s, k, str(v)])
            elif isinstance(items, dict):
                for k, v in items.items():
                    writer.writerow([s, k, str(v)])
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=my-data.csv"})
    return data

# ─── 3. DPO Contact ────────────────────────────────────────────────

@router.get("/dpo")
async def get_dpo_contact():
    return {
        "name": settings.dpo_name or "Ligerwave Data Protection Officer",
        "email": settings.dpo_email or "dpo@ligerwave.tech",
        "phone": settings.dpo_phone or None,
        "address": settings.dpo_address or None,
        "respond_within_days": 30,
        "jurisdiction": "South Africa (POPIA) / European Union (GDPR)",
    }

# ─── Existing endpoints below ───────────────────────────────────────

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
