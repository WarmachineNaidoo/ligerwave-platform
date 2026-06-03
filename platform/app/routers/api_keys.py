from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from app.database import supabase, service
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

class BulkKeyCreate(BaseModel):
    home_ids: List[str] = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=100)
    permissions: str = Field(default="read_only", pattern="^(read_only|dispatch|admin)$")
    expires_in_days: int = Field(default=365, ge=1, le=3650)

class KeyTransfer(BaseModel):
    new_home_id: str = Field(..., min_length=1)

@router.post("/bulk")
async def bulk_create_keys(
    body: BulkKeyCreate,
    payload: dict = Depends(get_current_user)
):
    user_id = payload.get("sub")
    user = service.table("users").select("organization_id,role").eq("id", user_id).execute()
    if not user.data or user.data[0].get("role") not in ("admin", "staff"):
        raise HTTPException(status_code=403, detail="Admin/staff access required")
    org_id = user.data[0].get("organization_id")
    keys = []
    for hid in body.home_ids:
        home = service.table("homes").select("id,organization_id").eq("id", hid).execute()
        if not home.data or home.data[0].get("organization_id") != org_id:
            continue
        raw_key = f"csi_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        expires_at = (datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)).isoformat()
        service.table("api_keys").insert({
            "home_id": hid,
            "label": body.label,
            "key_hash": key_hash,
            "permissions": body.permissions,
            "created_by": user_id,
            "expires_at": expires_at
        }).execute()
        keys.append({"home_id": hid, "key": raw_key})
    audit.log(user_id, "api_keys_bulk_created", "api_key", details={"count": len(keys), "label": body.label})
    return {"keys": keys, "total": len(keys)}

@router.post("/transfer/{key_id}")
async def transfer_key(
    key_id: str,
    body: KeyTransfer,
    payload: dict = Depends(get_current_user)
):
    user_id = payload.get("sub")
    user = service.table("users").select("organization_id,role").eq("id", user_id).execute()
    if not user.data or user.data[0].get("role") not in ("admin", "staff"):
        raise HTTPException(status_code=403, detail="Admin/staff access required")
    org_id = user.data[0].get("organization_id")
    key = service.table("api_keys").select("id,home_id").eq("id", key_id).execute()
    if not key.data:
        raise HTTPException(status_code=404, detail="Key not found")
    old_home = service.table("homes").select("organization_id").eq("id", key.data[0]["home_id"]).execute()
    new_home = service.table("homes").select("organization_id").eq("id", body.new_home_id).execute()
    if not old_home.data or not new_home.data:
        raise HTTPException(status_code=404, detail="Home not found")
    if old_home.data[0]["organization_id"] != org_id or new_home.data[0]["organization_id"] != org_id:
        raise HTTPException(status_code=403, detail="Both homes must be in your organization")
    service.table("api_keys").update({"home_id": body.new_home_id}).eq("id", key_id).execute()
    audit.log(user_id, "api_key_transferred", "api_key", resource_id=key_id, details={"from": key.data[0]["home_id"], "to": body.new_home_id})
    return {"status": "transferred", "key_id": key_id, "new_home_id": body.new_home_id}

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
    service.table("api_keys").insert({
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
    result = service.table("api_keys").select("id,label,permissions,expires_at,revoked,last_used_at,created_at").eq("home_id", home_id).execute()
    return result.data

@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user)
):
    key = service.table("api_keys").select("id,home_id").eq("id", key_id).execute()
    if not key.data:
        raise HTTPException(status_code=404, detail="Key not found")
    if key.data[0].get("home_id") != home_id:
        raise HTTPException(status_code=403, detail="Access denied")
    service.table("api_keys").update({"revoked": True}).eq("id", key_id).execute()
    audit.log(payload.get("sub"), "api_key_revoked", "api_key", resource_id=key_id)
    return {"status": "revoked"}
