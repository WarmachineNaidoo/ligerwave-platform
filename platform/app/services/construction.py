from typing import Dict, Optional
from datetime import datetime, timezone, timedelta
from app.services.mine import MineZone, mine_engine

class ConstructionSite:
    def __init__(self, site_id: str, name: str):
        self.site_id = site_id
        self.name = name
        self.zones: Dict[str, MineZone] = {}
        self.crane_zones: Dict[str, dict] = {}
        self.trench_zones: Dict[str, dict] = {}
        self.fall_events: list = []

    def get_zone(self, zone_id: str) -> MineZone:
        if zone_id not in self.zones:
            self.zones[zone_id] = MineZone(zone_id, zone_id)
        return self.zones[zone_id]

    def detect_fall(self, zone_id: str, vertical_movement: float, hr: Optional[float] = None) -> Optional[dict]:
        if vertical_movement > 2.0:
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "zone": zone_id,
                "vertical_movement": vertical_movement,
                "hr": hr,
                "severity": "critical" if hr is None or hr < 40 else "high" if hr > 100 else "medium",
                "harness_arrested": vertical_movement < 5.0,
            }
            self.fall_events.append(event)
            if len(self.fall_events) > 100:
                self.fall_events = self.fall_events[-50:]
            return event
        return None

    def check_crane_blind_spot(self, crane_id: str, person_distance: float, person_angle: int) -> dict:
        danger = person_distance < 5.0
        return {
            "crane_id": crane_id,
            "person_detected": person_distance > 0,
            "distance_m": round(person_distance, 1),
            "angle_deg": person_angle,
            "danger": danger,
            "alert": "Person in swing radius — halt" if danger else "Clear",
        }

    def check_trench(self, zone_id: str, vibration: float, occupancy: int) -> dict:
        collapse_risk = vibration > 0.8
        return {
            "zone": zone_id,
            "vibration_level": round(vibration, 3),
            "occupancy": occupancy,
            "collapse_risk": collapse_risk,
            "alert": "Collapse risk detected — evacuate" if collapse_risk else "Stable",
        }

    def detect_man_overboard(self, zone_id: str, person_present: bool, rail_proximity: float = 0) -> Optional[dict]:
        if not person_present and rail_proximity > 0.8:
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "zone": zone_id,
                "type": "man_overboard",
                "severity": "critical",
            }
            self.fall_events.append(event)
            return event
        return None

    def get_summary(self) -> dict:
        return {
            "site": self.name,
            "zones": {zid: {"occupancy": z.occupancy, "temp_c": z.temp_c} for zid, z in self.zones.items()},
            "fall_events_24h": sum(1 for e in self.fall_events if e["timestamp"] > (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()),
            "crane_zones": list(self.crane_zones.keys()),
            "trench_zones": list(self.trench_zones.keys()),
        }

sites: Dict[str, ConstructionSite] = {}
