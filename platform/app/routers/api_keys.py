from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.database import supabase
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from app.services.audit import audit
import hashlib, secrets
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

class ApiKeyCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    permissions: str = Field(default="read_only", pattern="^(read_only|dispatch|admin)$")
    expires_in_days: int = Field(default=365, ge=1, le=3650)

@router.post("")
async def create_api_key(
    body: ApiKeyCreate,
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user)
):
    user_id = payload.get("sub")
    raw_key = f"csi_{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)).isoformat()
    supabase.table("api_keys").insert({
        "home_id": home_id,
        "label": body.label,
        "key_hash": key_hash,
        "permissions": body.permissions,
        "created_by": user_id,
        "expires_at": expires_at
    }).execute()
    audit.log(user_id, "api_key_created", "api_key", details={"label": body.label, "permissions": body.permissions})
    return {"key": raw_key, "label": body.label, "permissions": body.permissions}

@router.get("")
async def list_api_keys(
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user)
):
    result = supabase.table("api_keys").select("id,label,permissions,expires_at,revoked,last_used_at,created_at").eq("home_id", home_id).execute()
    return result.data

@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user)
):
    key = supabase.table("api_keys").select("id,home_id").eq("id", key_id).execute()
    if not key.data:
        raise HTTPException(status_code=404, detail="Key not found")
    if key.data[0].get("home_id") != home_id:
        raise HTTPException(status_code=403, detail="Access denied")
    supabase.table("api_keys").update({"revoked": True}).eq("id", key_id).execute()
    audit.log(payload.get("sub"), "api_key_revoked", "api_key", resource_id=key_id)
    return {"status": "revoked"}
