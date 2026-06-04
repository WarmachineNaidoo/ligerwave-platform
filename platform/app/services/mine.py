from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
import numpy as np

class MineZone:
    def __init__(self, zone_id: str, name: str):
        self.zone_id = zone_id
        self.name = name
        self.hr_readings: List[tuple] = []
        self.gait_samples: List[tuple] = []
        self.occupancy = 0
        self.last_entry: Dict[str, datetime] = {}
        self.confined_space_timer: Optional[float] = None
        self.confined_space_worker: Optional[str] = None
        self.temp_c = 28.0
        self.hazard = False

    def log_hr(self, user_id: str, hr: float):
        now = datetime.now(timezone.utc)
        window = now - timedelta(minutes=30)
        self.hr_readings = [(t, u, h) for t, u, h in self.hr_readings if t > window.timestamp()]
        self.hr_readings.append((now.timestamp(), user_id, hr))

    def log_gait(self, user_id: str, stride_length: float, speed: float):
        now = datetime.now(timezone.utc)
        self.gait_samples.append((now.timestamp(), user_id, stride_length, speed))
        if len(self.gait_samples) > 1000:
            self.gait_samples = self.gait_samples[-500:]

    def fatigue_index(self, user_id: str) -> dict:
        user_gait = [(t, sl, sp) for t, _, sl, sp in self.gait_samples if _ == user_id][-50:]
        if len(user_gait) < 10:
            return {"fatigue": 0.0, "status": "insufficient_data", "baseline_stride": 0, "current_stride": 0}
        baseline_stride = np.mean([g[1] for g in user_gait[:10]])
        recent_stride = np.mean([g[1] for g in user_gait[-10:]])
        stride_ratio = recent_stride / max(baseline_stride, 0.01)
        heat_factor = max(0, (self.temp_c - 30) / 10) if self.temp_c > 30 else 0
        fatigue_score = min(1.0, max(0, (1 - stride_ratio) * 2 + heat_factor * 0.3))
        return {
            "fatigue": round(fatigue_score, 3),
            "status": "fatigued" if fatigue_score > 0.3 else "normal",
            "baseline_stride": round(baseline_stride, 3),
            "current_stride": round(recent_stride, 3),
            "heat_factor": round(heat_factor, 3),
            "temp_c": self.temp_c,
        }

    def heat_stress_risk(self, user_id: str) -> dict:
        user_hr = [(t, h) for t, u, h in self.hr_readings if u == user_id][-30:]
        if len(user_hr) < 5:
            return {"risk": "low", "status": "insufficient_data", "avg_hr": 0, "sustained_high_hr": False}
        avg_hr = np.mean([h for _, h in user_hr])
        sustained = sum(1 for _, h in user_hr if h > 100) > len(user_hr) * 0.5
        if avg_hr > 100 and sustained:
            return {"risk": "high", "status": "heat_stress_risk", "avg_hr": round(avg_hr), "sustained_high_hr": True, "recommendation": "Immediate rest and hydration"}
        if avg_hr > 85:
            return {"risk": "medium", "status": "monitoring", "avg_hr": round(avg_hr), "sustained_high_hr": sustained}
        return {"risk": "low", "status": "normal", "avg_hr": round(avg_hr), "sustained_high_hr": False}

    def enter_confined_space(self, user_id: str):
        self.confined_space_worker = user_id
        self.confined_space_timer = datetime.now(timezone.utc).timestamp()

    def exit_confined_space(self) -> Optional[dict]:
        if self.confined_space_timer:
            duration = datetime.now(timezone.utc).timestamp() - self.confined_space_timer
            result = {"worker": self.confined_space_worker, "duration_minutes": round(duration / 60, 1)}
            self.confined_space_timer = None
            self.confined_space_worker = None
            return result
        return None

    def confined_space_status(self) -> Optional[dict]:
        if self.confined_space_timer:
            duration = datetime.now(timezone.utc).timestamp() - self.confined_space_timer
            return {
                "worker": self.confined_space_worker,
                "duration_minutes": round(duration / 60, 1),
                "overdue": duration > 3600,
            }
        return None


class MineEngine:
    def __init__(self):
        self.zones: Dict[str, MineZone] = {}
        self.integrations = {"seismic": False, "gas": False, "ventilation": False, "blast": False, "dispatch": False}

    def get_zone(self, zone_id: str, name: str = "") -> MineZone:
        if zone_id not in self.zones:
            self.zones[zone_id] = MineZone(zone_id, name or zone_id)
        return self.zones[zone_id]

    def handle_seismic_event(self, magnitude: float, zone_id: str) -> dict:
        zone = self.get_zone(zone_id)
        alert = magnitude > 1.5
        return {"event": "seismic", "magnitude": magnitude, "zone": zone_id, "occupancy": zone.occupancy, "alert": alert}

    def handle_gas_alarm(self, gas_type: str, level: float, zone_id: str) -> dict:
        zone = self.get_zone(zone_id)
        return {"event": "gas_alarm", "gas_type": gas_type, "level": level, "zone": zone_id, "occupancy": zone.occupancy, "evacuate": level > 10}

    def get_summary(self) -> dict:
        return {
            "zones": {zid: {
                "name": z.name, "occupancy": z.occupancy,
                "temp_c": z.temp_c, "confined_space": z.confined_space_status(),
                "hazard": z.hazard,
            } for zid, z in self.zones.items()},
            "total_personnel": sum(z.occupancy for z in self.zones.values()),
            "active_confined_spaces": sum(1 for z in self.zones.values() if z.confined_space_status()),
            "hazard_zones": [zid for zid, z in self.zones.items() if z.hazard],
        }

mine_engine = MineEngine()
