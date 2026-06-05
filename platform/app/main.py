from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.config import settings as app_settings
from app.routers import auth, homes, devices, events, api_keys, arming, subscriptions, export, webhooks, agent, wellness, ar, settings, zones, push, health, premium, admin, privacy, tomography, prison, estate, mine, construction, payments
from app.services.ws import manager
from app.middleware.auth import get_current_user
from app.services.log import logger
from app.services.ratelimit import limiter, _get_client_ip
from app.services.breach import detector
import time, os, asyncio, uuid, json

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; connect-src 'self' https://zchqctktwkimfecmjnon.supabase.co wss://ligerwave.tech https://api.supabase.com; img-src 'self' data: https:; worker-src 'self'; manifest-src 'self'; form-action 'self'; base-uri 'self'; frame-ancestors 'none'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response

class AuthContextMiddleware(BaseHTTPMiddleware):
    """Extract user_id from JWT into request.state for logging (no verification)."""
    async def dispatch(self, request, call_next):
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                import base64
                payload_b64 = auth[7:].split(".")[1]
                payload_b64 += "=" * (4 - len(payload_b64) % 4)
                payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                request.state.user_id = payload.get("sub")
            except Exception as e:
                logger.warning("auth_context_decode_failed", extra={"extra": {"action": "decode_jwt", "error": str(e)}})
                request.state.user_id = None
        else:
            request.state.user_id = None
        return await call_next(request)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        req_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.error("request_failed", extra={"extra": {
                "request_id": req_id, "method": request.method,
                "path": request.url.path, "status": 500,
                "duration_ms": duration_ms, "ip": _get_client_ip(request)
            }})
            raise
        duration_ms = int((time.perf_counter() - start) * 1000)
        user_id = getattr(request.state, "user_id", None)
        logger.info("request", extra={"extra": {
            "request_id": req_id, "method": request.method,
            "path": request.url.path, "status": response.status_code,
            "duration_ms": duration_ms, "ip": _get_client_ip(request),
            "user_id": user_id,
        }})
        response.headers["X-Request-ID"] = req_id
        return response

class RequestBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 5 * 1024 * 1024:
            return Response("Request too large", status_code=413)
        return await call_next(request)

app = FastAPI(title="WiFi CSI Intrusion Detection Platform", version="0.1.0")

@app.on_event("startup")
async def start_escalation_ticker():
    """Periodically advance escalation tiers."""
    async def tick():
        while True:
            try:
                from app.services.escalation import escalation_protocols
                for proto in escalation_protocols.values():
                    proto.tick()
            except Exception as e:
                logger.warning("escalation_ticker_failed", extra={"extra": {"action": "tick_escalation", "error": str(e)}})
            await asyncio.sleep(30)
    asyncio.create_task(tick())

app.add_middleware(RequestBodySizeMiddleware)
cors_origins_list = [o.strip() for o in app_settings.cors_origins.split(",")]
allow_creds = not any(o == "*" for o in cors_origins_list)
app.add_middleware(CORSMiddleware, allow_origins=cors_origins_list, allow_credentials=allow_creds, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuthContextMiddleware)
app.add_middleware(LoggingMiddleware)

# Per-endpoint rate limits
limiter.set_limit("/auth/login", 10)
limiter.set_limit("/auth/register", 5)
limiter.set_limit("/auth/mfa", 5)
limiter.set_limit("/devices/events", 120)
limiter.set_limit("/devices", 30)
limiter.set_limit("/export", 10)
limiter.set_limit("/agent", 20)
limiter.set_limit("/webhooks", 20)
# Default for all others: 100
class PerEndpointRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp = limiter.check(request)
        if resp:
            detector.record_rate_limit(request.url.path, _get_client_ip(request))
            return resp
        return await call_next(request)
app.add_middleware(PerEndpointRateLimitMiddleware)

app.include_router(auth.router)
app.include_router(homes.router)
app.include_router(devices.router)
app.include_router(events.router)
app.include_router(api_keys.router)
app.include_router(arming.router)
app.include_router(subscriptions.router)
app.include_router(export.router)
app.include_router(webhooks.router)
app.include_router(agent.router)
app.include_router(wellness.router)
app.include_router(ar.router)
app.include_router(settings.router)
app.include_router(zones.router)
app.include_router(push.router)
app.include_router(health.router)
app.include_router(premium.router)
app.include_router(admin.router)
app.include_router(privacy.router)
app.include_router(tomography.router)
app.include_router(prison.router)
app.include_router(estate.router)
app.include_router(mine.router)
app.include_router(construction.router)
app.include_router(payments.router)

@app.websocket("/ws/{home_id}")
async def websocket_endpoint(websocket: WebSocket, home_id: str):
    """Real-time event push. First message must be {"type":"auth","token":"..."}."""
    try:
        data = await websocket.receive_text()
        msg = json.loads(data)
        if not isinstance(msg, dict) or msg.get("type") != "auth" or "token" not in msg:
            await websocket.close(code=4001)
            return
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{app_settings.supabase_url}/auth/v1/user", headers={"Authorization": f"Bearer {msg['token']}", "apikey": app_settings.supabase_key})
        if r.status_code != 200:
            await websocket.close(code=4001)
            return
        user_id = r.json().get("id")
        if not user_id:
            await websocket.close(code=4001)
            return
        # Verify user has access to this home
        user_org = service.table("users").select("organization_id").eq("id", user_id).execute()
        if user_org.data:
            org_id = user_org.data[0].get("organization_id")
            home_check = service.table("homes").select("id").eq("id", home_id).eq("organization_id", org_id).execute()
            if not home_check.data:
                await websocket.close(code=4001)
                return
        user_id = r.json().get("id")
        if not user_id:
            await websocket.close(code=4001)
            return
        await manager.connect(websocket, user_id, home_id)
        await websocket.send_json({"type": "connected", "home_id": home_id})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id if 'user_id' in dir() else "", home_id)
    except Exception as e:
        logger.warning("websocket_error", extra={"extra": {"action": "websocket_handler", "error": str(e)}})
        try:
            manager.disconnect(websocket, user_id if 'user_id' in dir() else "", home_id)
        except Exception as e2:
            logger.warning("websocket_disconnect_failed", extra={"extra": {"action": "disconnect_websocket", "error": str(e2)}})

@app.get("/health")
async def health():
    return {"status": "ok"}

static_dir = os.path.join(os.path.dirname(__file__), "static")
landing_path = os.path.join(static_dir, "landing.html")
if os.path.isfile(landing_path):
    from starlette.responses import HTMLResponse as HTMLResp
    @app.get("/", include_in_schema=False)
    async def serve_landing():
        with open(landing_path) as f:
            return HTMLResp(f.read())
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
