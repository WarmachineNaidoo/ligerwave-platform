from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, HttpUrl
from urllib.parse import urlparse
import ipaddress
from app.database import supabase, service
from app.middleware.auth import get_current_user, require_role
from app.middleware.ownership import verify_home_ownership
from app.services.audit import audit
from typing import Optional

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

def _validate_webhook_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        raise HTTPException(status_code=400, detail="Only HTTPS webhook URLs are allowed")
    host = parsed.hostname or ""
    if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254", "metadata.google.internal"):
        raise HTTPException(status_code=400, detail="Internal addresses not allowed")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise HTTPException(status_code=400, detail="Internal addresses not allowed")
    except ValueError:
        pass

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
    _validate_webhook_url(body.url)
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
