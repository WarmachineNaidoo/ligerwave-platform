from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from app.database import service
from httpx import AsyncClient
from app.config import settings
from datetime import datetime, timedelta, timezone
import hashlib, json, asyncio

router = APIRouter(prefix="/ar", tags=["ar"])

async def resolve_ar_access(request: Request, home_id: str = None):
    api_key = request.headers.get("x-api-key")
    auth_header = request.headers.get("Authorization", "")
    payload = None

    if api_key:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key = service.table("api_keys").select("home_id,permissions,expires_at,revoked").eq("key_hash", key_hash).execute()
        if not key.data:
            raise HTTPException(status_code=401, detail="Invalid API key")
        k = key.data[0]
        if k.get("revoked"):
            raise HTTPException(status_code=401, detail="API key revoked")
        if k.get("expires_at") and k["expires_at"] < datetime.now(timezone.utc).isoformat():
            raise HTTPException(status_code=401, detail="API key expired")
        if k["permissions"] not in ("read_only", "dispatch"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        if home_id and k["home_id"] != home_id:
            raise HTTPException(status_code=403, detail="Key not valid for this home")
        return {"type": "api_key", "home_id": k["home_id"], "permissions": k["permissions"]}

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        async with AsyncClient() as client:
            resp = await client.get(
                f"{settings.supabase_url}/auth/v1/user",
                headers={"Authorization": f"Bearer {token}", "apikey": settings.supabase_key}
            )
            if resp.status_code == 200:
                user_data = resp.json()
                payload = {"sub": user_data["id"], "email": user_data.get("email"), "role": "consumer"}

    if payload:
        user_id = payload.get("sub")
        role = payload.get("role", "consumer")
        user = service.table("users").select("organization_id").eq("id", user_id).execute()
        org_id = None
        if user.data and user.data[0].get("organization_id"):
            org_id = user.data[0]["organization_id"]
        accessible_homes = []
        if org_id:
            homes = service.table("homes").select("id").eq("organization_id", org_id).execute()
            accessible_homes = [h["id"] for h in homes.data or []]
        if home_id and home_id not in accessible_homes:
            raise HTTPException(status_code=403, detail="Access denied")
        return {"type": "jwt", "user_id": user_id, "organization_id": org_id, "accessible_homes": accessible_homes, "role": role}

    raise HTTPException(status_code=401, detail="Authentication required")

@router.get("/dispatch")
async def dispatch_list(request: Request):
    access = await resolve_ar_access(request)
    if access["type"] == "api_key":
        home = service.table("homes").select("id,name,address,status,created_at").eq("id", access["home_id"]).execute()
        return {"homes": home.data or []}

    org_id = access.get("organization_id")
    if not org_id:
        return {"homes": []}
    homes = service.table("homes").select("id,name,address,status,created_at").eq("organization_id", org_id).execute()
    return {"homes": homes.data or []}

@router.get("/dispatch/{home_id}/events")
async def dispatch_events(
    home_id: str,
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    event_type: str = Query(None),
):
    access = await resolve_ar_access(request, home_id)
    q = service.table("events").select("*").eq("home_id", home_id).order("timestamp", desc=True).limit(limit)
    if event_type:
        q = q.eq("event_type", event_type)
    events = q.execute()
    return {"home_id": home_id, "events": events.data or []}

@router.get("/dispatch/{home_id}/status")
async def dispatch_status(home_id: str, request: Request):
    access = await resolve_ar_access(request, home_id)
    home = service.table("homes").select("id,name,address,status").eq("id", home_id).execute()
    if not home.data:
        raise HTTPException(status_code=404, detail="Home not found")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = service.table("events").select("event_type,confidence,timestamp").eq("home_id", home_id).gte("timestamp", cutoff.isoformat()).order("timestamp", desc=True).limit(100).execute()
    events = recent.data or []

    last_event = events[0] if events else None
    intrusion_count = sum(1 for e in events if e.get("event_type") == "intrusion" and (e.get("confidence") or 0) >= 0.8)

    return {
        "home": home.data[0],
        "last_event": last_event,
        "intrusions_24h": intrusion_count,
        "events_24h": len(events),
        "status": home.data[0].get("status", "disarmed"),
    }

@router.get("/dispatch/{home_id}/live")
async def dispatch_live(home_id: str, request: Request):
    """SSE stream of live events for dispatchers."""
    access = await resolve_ar_access(request, home_id)
    if access["permissions"] not in ("dispatch", "admin"):
        raise HTTPException(status_code=403, detail="Dispatch access required")

    async def event_stream():
        last_id = None
        while True:
            try:
                q = service.table("events").select("*").eq("home_id", home_id).order("timestamp", desc=True).limit(1)
                if last_id:
                    q = q.gt("id", last_id)
                events = q.execute()
                for e in (events.data or []):
                    if last_id is None or e["id"] != last_id:
                        yield f"data: {json.dumps(e)}\n\n"
                        last_id = e["id"]
            except Exception:
                yield f"event: error\ndata: {json.dumps({'error': 'stream interrupted'})}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@router.post("/dispatch/{home_id}/acknowledge")
async def dispatch_acknowledge(home_id: str, request: Request):
    access = await resolve_ar_access(request, home_id)
    if access["permissions"] not in ("dispatch", "admin"):
        raise HTTPException(status_code=403, detail="Dispatch access required")
    body = await request.json()
    event_id = body.get("event_id")
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id required")
    service.table("events").update({"resolved_at": datetime.now(timezone.utc).isoformat(), "resolution": "dispatched"}).eq("id", event_id).execute()
    from app.services.escalation import escalation_protocols
    if home_id in escalation_protocols:
        escalation_protocols[home_id].acknowledge(event_id, "ar_dispatcher")
    return {"status": "acknowledged", "event_id": event_id}

@router.get("/dispatch/dashboard", include_in_schema=False)
async def dispatch_dashboard(request: Request):
    return HTMLResponse(open("app/static/dispatch.html").read())

@router.get("/keys")
async def ar_list_keys(request: Request):
    access = await resolve_ar_access(request)
    if access["type"] == "api_key":
        home = service.table("api_keys").select("id,label,permissions,expires_at,revoked,home_id,created_at").eq("home_id", access["home_id"]).execute()
        return {"keys": home.data or []}

    org_id = access.get("organization_id")
    if not org_id:
        return {"keys": []}
    homes = service.table("homes").select("id").eq("organization_id", org_id).execute()
    home_ids = [h["id"] for h in homes.data or []]
    if not home_ids:
        return {"keys": []}
    keys = service.table("api_keys").select("id,label,permissions,expires_at,revoked,home_id,created_at").in_("home_id", home_ids).execute()
    return {"keys": keys.data or []}

@router.put("/keys/{key_id}/revoke")
async def ar_revoke_key(key_id: str, request: Request):
    access = await resolve_ar_access(request)
    key = service.table("api_keys").select("id,home_id").eq("id", key_id).execute()
    if not key.data:
        raise HTTPException(status_code=404, detail="Key not found")
    if access["type"] == "api_key" and key.data[0].get("home_id") != access["home_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if access["type"] == "jwt":
        org_id = access.get("organization_id")
        homes = service.table("homes").select("id").eq("organization_id", org_id).execute()
        home_ids = [h["id"] for h in homes.data or []]
        if key.data[0].get("home_id") not in home_ids:
            raise HTTPException(status_code=403, detail="Access denied")
    service.table("api_keys").update({"revoked": True}).eq("id", key_id).execute()
    return {"status": "revoked"}
