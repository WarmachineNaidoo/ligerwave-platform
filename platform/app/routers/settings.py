from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.database import service
from app.middleware.auth import get_current_user
from app.config import settings as app_settings
from datetime import datetime, timezone, timedelta
import secrets, httpx

router = APIRouter(prefix="/settings", tags=["settings"])

def _admin_headers():
    return {"apikey": app_settings.supabase_service_key, "Authorization": "Bearer " + app_settings.supabase_service_key}

def get_meta(user_id: str) -> dict:
    r = httpx.get(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=_admin_headers())
    if r.status_code == 200:
        return r.json().get("user_metadata", {}) or {}
    return {}

def set_meta(user_id: str, data: dict):
    httpx.put(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers={**_admin_headers(), "Content-Type": "application/json"}, json={"user_metadata": data})

async def require_home_access(home_id: str = Query(...), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    user = service.table("users").select("organization_id").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=403, detail="User not found")
    org_id = user.data[0].get("organization_id")
    home = service.table("homes").select("id,organization_id").eq("id", home_id).execute()
    if not home.data:
        raise HTTPException(status_code=404, detail="Home not found")
    if home.data[0].get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return home_id

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)

@router.put("/profile")
async def update_profile(body: UpdateProfileRequest, payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    updates = {}
    if body.name:
        updates["name"] = body.name
    if updates:
        service.table("users").update(updates).eq("id", user_id).execute()
    return {"status": "updated"}

@router.get("/profile")
async def get_profile(payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    user = service.table("users").select("*").eq("id", user_id).execute()
    return (user.data or [{}])[0]

@router.delete("/account")
async def delete_account(payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    user = service.table("users").select("email,organization_id").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")
    email = user.data[0].get("email", "")
    org_id = user.data[0].get("organization_id")
    homes = service.table("homes").select("id").eq("organization_id", org_id).execute()
    for home in (homes.data or []):
        service.table("events").delete().eq("home_id", home["id"]).execute()
        service.table("devices").delete().eq("home_id", home["id"]).execute()
        service.table("api_keys").delete().eq("home_id", home["id"]).execute()
    service.table("homes").delete().eq("organization_id", org_id).execute()
    service.table("users").delete().eq("id", user_id).execute()
    return {"status": "deleted", "email": email}

# Email alerts via Supabase built-in email
@router.post("/notifications/email")
async def configure_email(body: dict, home_id: str = Depends(require_home_access), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = get_meta(user_id)
    notifs = meta.get("notifications", {})
    notifs["email"] = {"enabled": True, "home_id": home_id, "email": body.get("email", "")}
    meta["notifications"] = notifs
    set_meta(user_id, meta)
    return {"status": "configured"}

@router.post("/notifications/test")
async def test_notification(channel: str = Query(...), home_id: str = Depends(require_home_access), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = get_meta(user_id)
    notifs = meta.get("notifications", {})
    cfg = notifs.get(channel)
    if not cfg:
        raise HTTPException(status_code=400, detail=f"No config for channel {channel}")
    if channel == "email":
        user = service.table("users").select("email").eq("id", user_id).execute()
        to_email = cfg.get("email") or (user.data[0].get("email") if user.data else None)
        if to_email:
            import httpx as _httpx
            _h = {"apikey": app_settings.supabase_service_key, "Authorization": "Bearer " + app_settings.supabase_service_key, "Content-Type": "application/json"}
            try:
                _httpx.post(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}/email", json={"email": to_email}, headers=_h)
                return {"status": "sent"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    return {"status": "test_queued", "channel": channel}

# Notification config stored in user_metadata.notifications
@router.post("/notifications/telegram")
async def configure_telegram(body: dict, home_id: str = Depends(require_home_access), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = get_meta(user_id)
    notifs = meta.get("notifications", {})
    notifs["telegram"] = {"bot_token": body.get("bot_token"), "chat_id": body.get("chat_id"), "enabled": True, "home_id": home_id}
    meta["notifications"] = notifs
    set_meta(user_id, meta)
    return {"status": "configured"}

@router.post("/notifications/sms")
async def configure_sms(body: dict, home_id: str = Depends(require_home_access), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = get_meta(user_id)
    notifs = meta.get("notifications", {})
    notifs["sms"] = {"phone": body.get("phone"), "api_key": body.get("api_key"), "provider": body.get("provider", "clickatell"), "enabled": True, "home_id": home_id}
    meta["notifications"] = notifs
    set_meta(user_id, meta)
    return {"status": "configured"}

@router.get("/notifications")
async def get_notifications(home_id: str = Depends(require_home_access), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = get_meta(user_id)
    notifs = meta.get("notifications", {})
    result = []
    for channel, cfg in notifs.items():
        safe = {k: v for k, v in cfg.items() if k not in ("bot_token", "api_key")}
        result.append({"channel": channel, "enabled": cfg.get("enabled", True), "config": safe})
    return result

@router.delete("/notifications/{channel}")
async def remove_notification(channel: str, home_id: str = Depends(require_home_access), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = get_meta(user_id)
    notifs = meta.get("notifications", {})
    notifs.pop(channel, None)
    meta["notifications"] = notifs
    set_meta(user_id, meta)
    return {"status": "removed"}

# Family invites stored in user_metadata.invites
class FamilyInvite(BaseModel):
    email: str = Field(..., max_length=255)
    role: str = Field(default="read_only", pattern="^(read_only|dispatch|admin)$")

@router.post("/invites")
async def create_invite(body: FamilyInvite, home_id: str = Depends(require_home_access), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = get_meta(user_id)
    invites = meta.get("invites", [])
    invite = {
        "id": secrets.token_urlsafe(8),
        "home_id": home_id,
        "email": body.email,
        "role": body.role,
        "code": secrets.token_urlsafe(16),
        "created_by": user_id,
        "used": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    invites.append(invite)
    meta["invites"] = invites
    set_meta(user_id, meta)
    return {"invite_code": invite["code"], "email": body.email, "role": body.role}

@router.get("/invites")
async def list_invites(home_id: str = Depends(require_home_access), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = get_meta(user_id)
    home_invites = [i for i in (meta.get("invites") or []) if i.get("home_id") == home_id]
    return sorted(home_invites, key=lambda x: x.get("created_at", ""), reverse=True)

@router.delete("/invites/{invite_id}")
async def delete_invite(invite_id: str, home_id: str = Depends(require_home_access), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta = get_meta(user_id)
    invites = [i for i in (meta.get("invites") or []) if i.get("id") != invite_id]
    meta["invites"] = invites
    set_meta(user_id, meta)
    return {"status": "deleted"}

@router.post("/invites/accept")
async def accept_invite(code: str = Query(...), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    # Look up invite in all users' metadata (via admin API)
    r = httpx.get(f"{app_settings.supabase_url}/auth/v1/admin/users", headers=_admin_headers())
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Cannot list users")
    for u in r.json().get("users", []):
        meta = u.get("user_metadata") or {}
        for inv in (meta.get("invites") or []):
            if inv.get("code") == code and not inv.get("used"):
                if inv.get("expires_at", "") < datetime.now(timezone.utc).isoformat():
                    raise HTTPException(status_code=400, detail="Invite expired")
                home_id = inv["home_id"]
                home = service.table("homes").select("organization_id").eq("id", home_id).execute()
                if not home.data:
                    raise HTTPException(status_code=404, detail="Home not found")
                service.table("users").update({"organization_id": home.data[0]["organization_id"]}).eq("id", user_id).execute()
                inv["used"] = True
                inv["accepted_by"] = user_id
                meta["invites"] = [i for i in (meta.get("invites") or []) if i.get("id") != inv["id"]] + [inv]
                set_meta(u["id"], meta)
                return {"status": "accepted", "home_id": home_id}
    raise HTTPException(status_code=404, detail="Invalid invite code")
