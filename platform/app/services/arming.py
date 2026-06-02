from datetime import datetime, timezone
from typing import Dict, Optional
from app.database import service

class ArmingService:
    def is_armed(self, home_id: str) -> bool:
        home = service.table("homes").select("status").eq("id", home_id).execute()
        if not home.data:
            return False
        if home.data[0]["status"] == "armed":
            schedule = service.table("arming_schedules").select("*").eq("home_id", home_id).execute()
            if not schedule.data:
                return True
            s = schedule.data[0]
            if s.get("manual_override"):
                return s.get("manual_armed", False)
            now = datetime.now(timezone.utc)
            day = now.strftime("%A").lower()
            start = s.get(f"{day}_start")
            end = s.get(f"{day}_end")
            if not start or not end:
                return False
            current = now.strftime("%H:%M")
            return start <= current <= end
        return False

    def should_alert(self, home_id: str, confidence: float) -> bool:
        return self.is_armed(home_id) and confidence >= 0.92

arming = ArmingService()
