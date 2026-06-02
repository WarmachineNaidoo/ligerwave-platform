from datetime import datetime, timezone

class AuditLogger:
    def __init__(self):
        from app.database import service
        self.db = service

    def log(self, user_id: str, action: str, resource_type: str, resource_id: str = None, details: dict = None):
        self.db.table("audit_logs").insert({
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).execute()

audit = AuditLogger()
