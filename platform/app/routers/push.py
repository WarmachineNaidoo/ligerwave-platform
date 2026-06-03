from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from app.database import service
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from app.config import settings as app_settings
import json, httpx, os

router = APIRouter(prefix="/push", tags=["push"])

def _headers():
    return {"apikey": app_settings.supabase_service_key, "Authorization": "Bearer " + app_settings.supabase_service_key}

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict
    home_id: str

@router.post("/subscribe")
async def subscribe(body: PushSubscription, payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta_r = httpx.get(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=_headers())
    meta = meta_r.json().get("user_metadata", {}) or {} if meta_r.status_code == 200 else {}
    subs = meta.get("push_subscriptions", [])
    subs = [s for s in subs if s.get("endpoint") != body.endpoint]
    subs.append({"endpoint": body.endpoint, "keys": body.keys.model_dump() if hasattr(body.keys, 'model_dump') else body.keys, "home_id": body.home_id, "created_at": __import__('datetime').datetime.now().isoformat()})
    meta["push_subscriptions"] = subs
    httpx.put(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers={**_headers(), "Content-Type": "application/json"}, json={"user_metadata": meta})
    return {"status": "subscribed"}

@router.delete("/unsubscribe")
async def unsubscribe(endpoint: str = Query(...), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta_r = httpx.get(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=_headers())
    meta = meta_r.json().get("user_metadata", {}) or {} if meta_r.status_code == 200 else {}
    subs = [s for s in (meta.get("push_subscriptions") or []) if s.get("endpoint") != endpoint]
    meta["push_subscriptions"] = subs
    httpx.put(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers={**_headers(), "Content-Type": "application/json"}, json={"user_metadata": meta})
    return {"status": "unsubscribed"}

@router.get("/vapid-key")
async def get_vapid_key():
    key = os.environ.get("VAPID_PUBLIC_KEY", "BJlZ7G1vYTt3Jw0F5qLqXxHjGKA3cBz1V0RdYmR8M9s2Q4WmNvYxLpPqRsTuVwXyZ")
    return {"public_key": key}
