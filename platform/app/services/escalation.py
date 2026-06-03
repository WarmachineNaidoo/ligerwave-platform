from typing import Dict, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from app.database import service
from app.config import settings as app_settings
import json, httpx, time
from app.services.log import logger

class EscalationProtocol:
    """Configurable escalation chain for critical events.
    
    Tiers:
      tier_1: User (SMS/push/email) — immediate notification
      tier_2: Next of kin (SMS/push/email) — after no user response for N seconds
      tier_3: AR company (API/webhook) — after next of kin timeout
      tier_4: Authorities (API/email) — after AR timeout
    
    Each tier has configurable timeout, channels, and contacts.
    """

    def __init__(self, home_id: str):
        self.home_id = home_id
        self._config = self._load_config()
        self._active_alerts: Dict[str, Dict] = {}  # event_id -> alert state

    def _load_config(self) -> Dict:
        """Load escalation config from home metadata."""
        home = service.table("homes").select("escalation_config").eq("id", self.home_id).execute()
        if home.data and home.data[0].get("escalation_config"):
            return home.data[0]["escalation_config"]
        return {
            "enabled": False,
            "tiers": [
                {"name": "user", "timeout_seconds": 120, "channels": ["push", "sms", "email"]},
                {"name": "next_of_kin", "timeout_seconds": 300, "channels": ["sms", "email"]},
                {"name": "ar_company", "timeout_seconds": 600, "channels": ["webhook", "email"]},
                {"name": "authorities", "timeout_seconds": 0, "channels": ["email", "sms"]},
            ],
            "contacts": {
                "user": {"phone": "", "email": ""},
                "next_of_kin": {"name": "", "phone": "", "email": ""},
                "ar_company": {"webhook_url": "", "email": ""},
                "authorities": {"email": "", "phone": ""},
            },
            "event_types": {
                "fall": True,
                "stopped_breathing": True,
                "intrusion": True,
                "apnea_severe": False,
            }
        }

    def save_config(self, config: Dict):
        service.table("homes").update({"escalation_config": config}).eq("id", self.home_id).execute()
        self._config = config

    def get_config(self) -> Dict:
        return self._config

    def trigger(self, event_id: str, event_type: str, confidence: float, details: Dict = None):
        """Start escalation for a critical event."""
        if not self._config.get("enabled"):
            return {"escalated": False, "reason": "escalation_disabled"}

        allowed = self._config.get("event_types", {})
        if not allowed.get(event_type, False):
            return {"escalated": False, "reason": "event_type_not_enabled"}

        alert = {
            "event_id": event_id,
            "event_type": event_type,
            "confidence": confidence,
            "details": details or {},
            "started_at": datetime.now(timezone.utc).isoformat(),
            "current_tier": 0,
            "tier_started_at": datetime.now(timezone.utc).isoformat(),
            "resolved": False,
            "acknowledged_by": None,
        }
        self._active_alerts[event_id] = alert
        self._notify_tier(0, alert)
        return {"escalated": True, "alert_id": event_id, "tier": 0}

    def acknowledge(self, event_id: str, by: str = "user"):
        """Acknowledge an alert, stopping escalation."""
        if event_id in self._active_alerts:
            self._active_alerts[event_id]["resolved"] = True
            self._active_alerts[event_id]["acknowledged_by"] = by
        return {"acknowledged": True}

    def tick(self):
        """Called periodically to advance escalation tiers."""
        now = datetime.now(timezone.utc)
        for event_id, alert in list(self._active_alerts.items()):
            if alert.get("resolved"):
                continue
            tiers = self._config.get("tiers", [])
            current_tier = alert.get("current_tier", 0)
            if current_tier >= len(tiers) - 1:
                continue
            tier_config = tiers[current_tier]
            timeout = tier_config.get("timeout_seconds", 120)
            tier_start = datetime.fromisoformat(alert.get("tier_started_at", now.isoformat()))
            if (now - tier_start).total_seconds() >= timeout:
                next_tier = current_tier + 1
                alert["current_tier"] = next_tier
                alert["tier_started_at"] = now.isoformat()
                self._notify_tier(next_tier, alert)

    def _notify_tier(self, tier_idx: int, alert: Dict):
        """Send notification for a given escalation tier."""
        tiers = self._config.get("tiers", [])
        if tier_idx >= len(tiers):
            return
        tier = tiers[tier_idx]
        contacts = self._config.get("contacts", {})
        tier_name = tier.get("name", f"tier_{tier_idx}")
        contact = contacts.get(tier_name, {})
        event_type = alert.get("event_type", "unknown")
        confidence = alert.get("confidence", 0)
        msg = f"Ligerwave Alert: {event_type.upper()} detected ({round(confidence*100)}% confidence) at {alert.get('started_at', '')}"

        channels = tier.get("channels", [])
        for channel in channels:
            if channel == "push":
                self._send_push(tier_name, msg, alert)
            elif channel == "sms" and contact.get("phone"):
                self._send_sms(contact["phone"], msg)
            elif channel == "email" and contact.get("email"):
                self._send_email(contact["email"], f"Ligerwave {event_type} Alert", msg)
            elif channel == "webhook" and contact.get("webhook_url"):
                self._send_webhook(contact["webhook_url"], alert)
        # Log the escalation event
        try:
            service.table("events").insert({
                "home_id": self.home_id,
                "event_type": "escalation",
                "confidence": confidence,
                "metadata": {"tier": tier_name, "alert_id": alert.get("event_id"), "channels": channels, "message": msg}
            }).execute()
        except Exception as e:
            logger.warning("escalation_log_failed", extra={"extra": {"action": "log_escalation_event", "error": str(e)}})

    def _send_push(self, tier: str, message: str, alert: Dict):
        """Send to all push subscribers for this home."""
        try:
            # Find users with push subscriptions for this home
            users_r = httpx.get(f"{app_settings.supabase_url}/auth/v1/admin/users", headers={"apikey": app_settings.supabase_service_key, "Authorization": "Bearer " + app_settings.supabase_service_key})
            if users_r.status_code != 200:
                return
            for u in users_r.json().get("users", []):
                meta = u.get("user_metadata") or {}
                for sub in (meta.get("push_subscriptions") or []):
                    if sub.get("home_id") == self.home_id:
                        self._send_webpush(sub, message, alert)
        except Exception as e:
            logger.warning("escalation_push_failed", extra={"extra": {"action": "send_push", "tier": tier, "error": str(e)}})

    def _send_webpush(self, subscription: Dict, message: str, alert: Dict):
        """Send a web push notification using the Web Push API."""
        try:
            # Use VAPID key from env
            vapid_private = __import__('os').environ.get("VAPID_PRIVATE_KEY", "")
            if not vapid_private:
                return
            from cryptography.fernet import Fernet
            # Simple push via HTTP POST to the endpoint
            endpoint = subscription.get("endpoint", "")
            keys = subscription.get("keys", {})
            if not endpoint or not keys:
                return
            if not endpoint.startswith("https://"):
                logger.warning("webpush_invalid_endpoint", extra={"extra": {"action": "send_webpush", "endpoint": endpoint[:80]}})
                return
            payload = json.dumps({"title": "Ligerwave Alert", "body": message, "tag": "ligerwave-escalation"}).encode()
            httpx.post(endpoint, content=payload, headers={"Content-Type": "application/json", "TTL": "86400"})
        except Exception as e:
            logger.warning("escalation_webpush_failed", extra={"extra": {"action": "send_webpush", "error": str(e)}})

    def _send_sms(self, phone: str, message: str):
        try:
            httpx.post(f"https://api.clickatell.com/rest/message", json={"text": message, "to": [phone]}, headers={"Authorization": "Bearer DUMMY", "Content-Type": "application/json"}, timeout=5)
        except Exception as e:
            logger.warning("escalation_sms_failed", extra={"extra": {"action": "send_sms", "phone": phone[-4:], "error": str(e)}})

    def _send_email(self, to_email: str, subject: str, body: str):
        try:
            httpx.post(f"{app_settings.supabase_url}/auth/v1/admin/users/email", json={"email": to_email, "subject": subject, "body": body}, headers={"apikey": app_settings.supabase_service_key, "Authorization": "Bearer " + app_settings.supabase_service_key, "Content-Type": "application/json"}, timeout=5)
        except Exception as e:
            logger.warning("escalation_email_failed", extra={"extra": {"action": "send_email", "email": to_email, "error": str(e)}})

    def _send_webhook(self, url: str, alert: Dict):
        try:
            httpx.post(url, json={"type": "escalation", "alert": alert}, timeout=5)
        except Exception as e:
            logger.warning("escalation_webhook_failed", extra={"extra": {"action": "send_webhook", "url": url[:80], "error": str(e)}})


escalation_protocols: Dict[str, EscalationProtocol] = {}
