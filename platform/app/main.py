from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.config import settings
from app.routers import auth, homes, devices, events, api_keys, arming, subscriptions, export, webhooks
import time, os

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-XSS-Protection"] = "0"
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    async def dispatch(self, request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        key = f"{client_ip}:{request.url.path}"
        window = self.requests.get(key, [])
        window = [t for t in window if now - t < self.window_seconds]
        if len(window) >= self.max_requests:
            return Response(status_code=429, content="Too many requests")
        window.append(now)
        self.requests[key] = window
        return await call_next(request)

app = FastAPI(title="WiFi CSI Intrusion Detection Platform", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(SecurityHeadersMiddleware)

if settings.environment == "production":
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.cors_origins.split(","))

app.include_router(auth.router)
app.include_router(homes.router)
app.include_router(devices.router)
app.include_router(events.router)
app.include_router(api_keys.router)
app.include_router(arming.router)
app.include_router(subscriptions.router)
app.include_router(export.router)
app.include_router(webhooks.router)

@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.environment}

import shutil
static_dir = os.path.join(os.path.dirname(__file__), "static")
dashboard_path = os.path.join(static_dir, "dashboard.html")
index_path = os.path.join(static_dir, "index.html")
if os.path.isfile(dashboard_path) and not os.path.isfile(index_path):
    shutil.copy2(dashboard_path, index_path)
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
