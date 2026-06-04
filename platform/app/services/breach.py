import time
from typing import Dict, List
from collections import defaultdict
from datetime import datetime, timezone
from app.services.log import logger
from app.database import service
from app.config import settings

BREACH_WINDOW_SECONDS = 300
AUTH_FAIL_THRESHOLD = 20
RATE_LIMIT_THRESHOLD = 50
ANOMALY_THRESHOLD = 0.95

class BreachDetector:
    def __init__(self):
        self._auth_fails: Dict[str, List[float]] = defaultdict(list)
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)
        self._last_breach_time: Dict[str, float] = {}
        self._cool_down_seconds = 3600

    def record_auth_failure(self, ip: str = "unknown", email: str = ""):
        now = time.time()
        self._auth_fails[ip] = [t for t in self._auth_fails[ip] if now - t < BREACH_WINDOW_SECONDS]
        self._auth_fails[ip].append(now)
        fail_count = len(self._auth_fails[ip])
        if fail_count >= AUTH_FAIL_THRESHOLD and now - self._last_breach_time.get(f"auth:{ip}", 0) > self._cool_down_seconds:
            self._raise_breach("auth_brute_force", {
                "ip": ip, "fail_count": fail_count, "window_seconds": BREACH_WINDOW_SECONDS
            })

    def record_rate_limit(self, path: str, ip: str = "unknown"):
        now = time.time()
        key = f"{ip}:{path}"
        self._rate_limits[key] = [t for t in self._rate_limits[key] if now - t < BREACH_WINDOW_SECONDS]
        self._rate_limits[key].append(now)
        count = len(self._rate_limits[key])
        if count >= RATE_LIMIT_THRESHOLD and now - self._last_breach_time.get(f"ratelimit:{key}", 0) > self._cool_down_seconds:
            self._raise_breach("rate_limit_spike", {
                "ip": ip, "path": path, "request_count": count, "window_seconds": BREACH_WINDOW_SECONDS
            })

    def _raise_breach(self, breach_type: str, details: dict):
        now = time.time()
        key = f"{breach_type}:{details.get('ip', 'unknown')}"
        self._last_breach_time[key] = now
        severity = "critical" if breach_type == "auth_brute_force" else "high"
        breach_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "breach_type": breach_type,
            "severity": severity,
            "details": details,
        }
        service.table("audit_logs").insert({
            "user_id": None,
            "action": f"breach_{breach_type}",
            "resource_type": "security",
            "resource_id": f"{breach_type}_{int(now)}",
            "details": breach_record,
            "ip_address": details.get("ip", "unknown"),
        }).execute()
        logger.critical("breach_detected", extra={"extra": breach_record})
        if settings.breach_webhook_url:
            try:
                import httpx
                httpx.post(settings.breach_webhook_url, json={
                    "event": "breach",
                    "breach_type": breach_type,
                    "severity": severity,
                    "details": details,
                    "dpo_email": settings.dpo_email,
                }, timeout=10)
            except Exception as e:
                logger.warning("breach_webhook_failed", extra={"extra": {"error": str(e)}})

detector = BreachDetector()
