from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, HttpUrl
from app.database import supabase, service
from app.middleware.auth import get_current_user, require_role
from app.middleware.ownership import verify_home_ownership
from app.services.audit import audit
from typing import Optional

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

class WebhookConfig(BaseModel):
    url: str = Field(..., max_length=500)
    event_types: list[str] = Field(default=["intrusion"], max_length=10)
    min_confidence: float = Field(default=0.92, ge=0, le=1)

@router.post("/{home_id}")
async def create_webhook(
    body: WebhookConfig,
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user),
):
    existing = service.table("webhooks").select("*").eq("home_id", home_id).execute()
    if existing.data:
        service.table("webhooks").update(body.model_dump()).eq("home_id", home_id).execute()
    else:
        body_dict = body.model_dump()
        body_dict["home_id"] = home_id
        service.table("webhooks").insert(body_dict).execute()
    audit.log(payload.get("sub"), "webhook_configured", "webhook", resource_id=home_id)
    return {"status": "configured", "url": body.url}

@router.get("/{home_id}")
async def get_webhook(home_id: str = Depends(verify_home_ownership)):
    result = service.table("webhooks").select("*").eq("home_id", home_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No webhook configured")
    return result.data[0]

@router.delete("/{home_id}")
async def delete_webhook(
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user),
):
    service.table("webhooks").delete().eq("home_id", home_id).execute()
    audit.log(payload.get("sub"), "webhook_deleted", "webhook", resource_id=home_id)
    return {"status": "deleted"}
