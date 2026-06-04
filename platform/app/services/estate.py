from typing import Dict, List
from datetime import datetime, timezone
from app.database import service

class EstatePerimeter:
    def __init__(self, estate_id: str):
        self.estate_id = estate_id
        self.zones: Dict[str, dict] = {}
        self.patrol_routes: Dict[str, List[str]] = {}
        self.guard_locations: Dict[str, dict] = {}

    def add_zone(self, zone_id: str, zone_type: str, sensitivity: float = 0.8, coord_path: List[tuple] = None):
        self.zones[zone_id] = {
            "zone_type": zone_type,
            "sensitivity": sensitivity,
            "coord_path": coord_path or [],
        }

    def get_perimeter_summary(self) -> dict:
        alerts = []
        for hid, home in self.zones.items():
            events = service.table("events").select("event_type,confidence,zone,timestamp").eq("home_id", hid).gte("timestamp", "now() - interval '1 hour'").order("timestamp", desc=True).limit(10).execute()
            zone_alerts = [e for e in (events.data or []) if e.get("confidence", 0) >= self.zones[hid].get("sensitivity", 0.8)]
            if zone_alerts:
                alerts.append({"zone": hid, "alerts": zone_alerts[:3], "zone_type": self.zones[hid]["zone_type"]})
        return {"estate_id": self.estate_id, "active_alerts": len(alerts), "alerts": alerts[:10]}

estates: Dict[str, EstatePerimeter] = {}
