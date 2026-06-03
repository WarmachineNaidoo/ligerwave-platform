import numpy as np
from typing import Dict, List, Optional
from collections import deque
from datetime import datetime, timezone
from app.database import service


class DoorWindowDetector:
    def __init__(self, home_id: str, window_size: int = 50):
        self.home_id = home_id
        self.window_size = window_size
        self.buffer: deque = deque(maxlen=window_size)
        self.baseline: Optional[float] = None
        self.last_event: float = 0

    def add_packet(self, amplitude: np.ndarray):
        mean_amp = float(np.mean(np.abs(amplitude)))
        self.buffer.append(mean_amp)
        if len(self.buffer) < 20:
            return
        if self.baseline is None:
            self.baseline = float(np.mean(list(self.buffer)[:15]))
        recent = np.array(list(self.buffer))[-10:]
        delta = abs(float(np.mean(recent)) - self.baseline) / max(self.baseline, 1e-8)
        now = datetime.now(timezone.utc).timestamp()
        if delta > 0.15 and (now - self.last_event) > 30:
            self.last_event = now
            self.baseline = float(np.mean(recent))
            service.table("events").insert({
                "home_id": self.home_id, "event_type": "door_window",
                "confidence": min(1.0, delta), "zone": "premium",
                "metadata": {"delta": round(delta, 3)}
            }).execute()

    def get_status(self) -> Dict:
        return {"enabled": True, "events_tracked": len(self.buffer), "baseline": self.baseline}


class VehicleDetector:
    def __init__(self, home_id: str, window_size: int = 200):
        self.home_id = home_id
        self.window_size = window_size
        self.buffer: deque = deque(maxlen=window_size)
        self.last_event: float = 0

    def add_packet(self, amplitude: np.ndarray):
        mean_amp = float(np.mean(np.abs(amplitude)))
        self.buffer.append(mean_amp)
        if len(self.buffer) < 50:
            return
        arr = np.array(list(self.buffer))
        recent = arr[-20:]
        older = arr[-60:-40]
        drift = float(np.mean(recent) - np.mean(older))
        now = datetime.now(timezone.utc).timestamp()
        if abs(drift) > 0.25 and (now - self.last_event) > 120:
            self.last_event = now
            direction = "arrival" if drift > 0 else "departure"
            service.table("events").insert({
                "home_id": self.home_id, "event_type": "vehicle",
                "confidence": min(1.0, abs(drift)), "zone": "premium",
                "metadata": {"direction": direction, "drift": round(drift, 3)}
            }).execute()

    def get_status(self) -> Dict:
        return {"enabled": True, "events_tracked": len(self.buffer)}


class FireSmokeDetector:
    def __init__(self, home_id: str, window_size: int = 100):
        self.home_id = home_id
        self.window_size = window_size
        self.buffer: deque = deque(maxlen=window_size)
        self.variance_baseline: Optional[float] = None

    def add_packet(self, amplitude: np.ndarray):
        var = float(np.var(amplitude))
        self.buffer.append(var)
        if len(self.buffer) < 30:
            return
        if self.variance_baseline is None:
            self.variance_baseline = float(np.mean(list(self.buffer)[:20]))
        recent = np.array(list(self.buffer))[-15:]
        ratio = float(np.mean(recent)) / max(self.variance_baseline, 1e-8)
        if ratio > 3.0:
            service.table("events").insert({
                "home_id": self.home_id, "event_type": "fire_smoke",
                "confidence": min(1.0, ratio / 5.0), "zone": "premium",
                "metadata": {"variance_ratio": round(ratio, 2)}
            }).execute()

    def get_status(self) -> Dict:
        return {"enabled": True, "variance_baseline": self.variance_baseline}


class HeartRateDetector:
    def __init__(self, home_id: str, window_size: int = 300, sample_rate: float = 10):
        self.home_id = home_id
        self.window_size = window_size
        self.sample_rate = sample_rate
        self.buffer: deque = deque(maxlen=window_size)

    def add_packet(self, amplitude: np.ndarray):
        phase = np.angle(amplitude)
        self.buffer.append(float(np.mean(phase)))

    def detect(self) -> Dict:
        if len(self.buffer) < self.window_size // 2:
            return {"heart_rate_bpm": None, "confidence": 0, "status": "buffering"}
        arr = np.array(list(self.buffer))
        arr -= np.mean(arr)
        window = np.hamming(len(arr))
        fft = np.abs(np.fft.rfft(arr * window))
        freqs = np.fft.rfftfreq(len(arr), d=1/self.sample_rate)
        mask = (freqs >= 0.8) & (freqs <= 3.0)
        if not np.any(mask):
            return {"heart_rate_bpm": None, "confidence": 0, "status": "no_signal"}
        peak_idx = np.argmax(fft * mask)
        hr = freqs[peak_idx] * 60
        total_power = np.sum(fft[mask])
        noise_power = np.sum(fft[~mask]) if np.any(~mask) else 1e-10
        confidence = min(1.0, total_power / max(noise_power, 1e-10))
        return {"heart_rate_bpm": round(hr, 1), "confidence": round(confidence, 3), "status": "active"}

    def get_status(self) -> Dict:
        return {"enabled": True, "samples": len(self.buffer)}


class GaitDetector:
    def __init__(self, home_id: str, window_size: int = 50):
        self.home_id = home_id
        self.window_size = window_size
        self.buffer: deque = deque(maxlen=window_size)
        self.fingerprints: Dict[str, np.ndarray] = {}
        self.last_learn: float = 0

    def add_packet(self, amplitude: np.ndarray):
        self.buffer.append(amplitude.ravel())

    def detect(self) -> Dict:
        if len(self.buffer) < 20:
            return {"status": "learning", "gait_match": None, "confidence": 0}
        stacked = np.stack(list(self.buffer))
        diffs = np.sum(np.abs(np.diff(stacked, axis=0)), axis=1)
        # Detect walking bouts (periodic bursts of diff energy)
        threshold = float(np.percentile(diffs, 85))
        steps = diffs > threshold
        if np.sum(steps) < 5:
            return {"status": "idle", "gait_match": None, "confidence": 0}
        # Extract cadence from step interval
        step_indices = np.where(steps)[0]
        intervals = np.diff(step_indices)
        cadence = float(np.mean(intervals)) if len(intervals) > 0 else 0
        # Simple signature: mean + std of frame diffs during walk
        gait_sig = np.array([float(np.mean(diffs[steps])), float(np.std(diffs[steps])), cadence])
        # Match against known fingerprints
        best_match = None
        best_score = 0
        for label, fp in self.fingerprints.items():
            score = 1.0 / (1.0 + float(np.linalg.norm(gait_sig - fp)))
            if score > best_score:
                best_score = score
                best_match = label
        if best_score > 0.6:
            return {"status": "active", "gait_match": best_match, "confidence": round(best_score, 3)}
        return {"status": "unknown", "gait_match": None, "confidence": round(best_score, 3)}

    def learn(self, label: str):
        if len(self.buffer) < 20:
            return {"error": "insufficient_data"}
        stacked = np.stack(list(self.buffer))
        diffs = np.sum(np.abs(np.diff(stacked, axis=0)), axis=1)
        steps = diffs > np.percentile(diffs, 85)
        if np.sum(steps) < 5:
            return {"error": "no_walk_detected"}
        step_indices = np.where(steps)[0]
        intervals = np.diff(step_indices)
        cadence = float(np.mean(intervals)) if len(intervals) > 0 else 0
        self.fingerprints[label] = np.array([float(np.mean(diffs[steps])), float(np.std(diffs[steps])), cadence])
        service.table("events").insert({
            "home_id": self.home_id, "event_type": "gait_learned",
            "confidence": 1.0, "zone": "premium",
            "metadata": {"label": label}
        }).execute()
        return {"learned": label}

    def get_status(self) -> Dict:
        return {"enabled": True, "known_gait": list(self.fingerprints.keys())}


class RoutineDeviationDetector:
    def __init__(self, home_id: str):
        self.home_id = home_id
        self.hourly_profile: Dict[int, float] = {}  # hour -> avg event count

    def add_event(self, event_type: str, confidence: float):
        hour = datetime.now(timezone.utc).hour
        self.hourly_profile[hour] = self.hourly_profile.get(hour, 0) * 0.9 + 0.1

    def check(self) -> Dict:
        hour = datetime.now(timezone.utc).hour
        expected = self.hourly_profile.get(hour, 0)
        if expected < 1:
            return {"deviation": 0, "status": "learning"}
        # Count recent events in this hour
        cutoff = (datetime.now(timezone.utc).timestamp() - 3600)
        recent = service.table("events").select("id").eq("home_id", self.home_id).gte("timestamp", datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat()).execute()
        count = len(recent.data or [])
        deviation = abs(count - expected) / max(expected, 1)
        if deviation > 2.0:
            service.table("events").insert({
                "home_id": self.home_id, "event_type": "routine_deviation",
                "confidence": min(1.0, deviation / 4.0), "zone": "premium",
                "metadata": {"expected": round(expected, 1), "actual": count}
            }).execute()
        return {"deviation": round(deviation, 2), "expected": round(expected, 1), "actual": count}

    def get_status(self) -> Dict:
        return {"enabled": True, "hours_learned": len(self.hourly_profile)}


class BabyCryDetector:
    def __init__(self, home_id: str, window_size: int = 100):
        self.home_id = home_id
        self.window_size = window_size
        self.buffer: deque = deque(maxlen=window_size)

    def add_packet(self, amplitude: np.ndarray):
        # Cry causes high-frequency micro-vibrations in CSI
        high_freq_energy = float(np.std(np.diff(amplitude.ravel())))
        self.buffer.append(high_freq_energy)
        if len(self.buffer) < 30:
            return
        arr = np.array(list(self.buffer))
        recent = arr[-15:]
        baseline = float(np.median(arr[:-15])) if len(arr) > 15 else 0.01
        ratio = float(np.mean(recent)) / max(baseline, 1e-8)
        if ratio > 2.5:
            service.table("events").insert({
                "home_id": self.home_id, "event_type": "baby_cry",
                "confidence": min(1.0, ratio / 4.0), "zone": "premium",
                "metadata": {"energy_ratio": round(ratio, 2)}
            }).execute()

    def get_status(self) -> Dict:
        return {"enabled": True, "samples": len(self.buffer)}


class RoomOccupancyDetector:
    def __init__(self, home_id: str):
        self.home_id = home_id
        self.zones: Dict[str, deque] = {}

    def add_packet(self, amplitude: np.ndarray, zone: str = "default"):
        mean_motion = float(np.mean(np.abs(np.diff(amplitude.ravel()))))
        if zone not in self.zones:
            self.zones[zone] = deque(maxlen=30)
        self.zones[zone].append(mean_motion)

    def estimate(self) -> Dict:
        occupancy = {}
        for zone, buf in self.zones.items():
            if len(buf) < 10:
                occupancy[zone] = 0
                continue
            activity = float(np.mean(list(buf)))
            occupancy[zone] = min(5, int(activity / 0.05))
        return {"occupancy": occupancy, "total": sum(occupancy.values())}

    def get_status(self) -> Dict:
        return {"enabled": True, "zones_monitored": list(self.zones.keys())}


class SmartTriggers:
    def __init__(self, home_id: str):
        self.home_id = home_id
        self.triggers: List[Dict] = []

    def set_trigger(self, trigger: Dict):
        self.triggers.append(trigger)

    def add_event(self, event_type: str, confidence: float):
        for t in self.triggers:
            if t.get("on_event") == event_type and confidence >= t.get("min_confidence", 0.5):
                service.table("events").insert({
                    "home_id": self.home_id, "event_type": "smart_trigger",
                    "confidence": confidence, "zone": "premium",
                    "metadata": {"trigger_name": t.get("name", ""), "action": t.get("action", "")}
                }).execute()

    def get_status(self) -> Dict:
        return {"enabled": True, "triggers_configured": len(self.triggers)}


class WaterLeakDetector:
    def __init__(self, home_id: str, window_size: int = 300):
        self.home_id = home_id
        self.window_size = window_size
        self.buffer: deque = deque(maxlen=window_size)
        self.baseline: Optional[float] = None

    def add_packet(self, amplitude: np.ndarray):
        mean_amp = float(np.mean(np.abs(amplitude)))
        self.buffer.append(mean_amp)
        if len(self.buffer) < 100:
            return
        if self.baseline is None:
            self.baseline = float(np.median(list(self.buffer)))
        recent = np.array(list(self.buffer))[-30:]
        attenuation = float(np.median(recent)) / max(self.baseline, 1e-8)
        # Water leak = persistent, slowly increasing attenuation (not sudden like door)
        recent_std = float(np.std(recent))
        if attenuation < 0.8 and recent_std < 0.02 and (self.baseline - float(np.median(recent))) > 0.05:
            service.table("events").insert({
                "home_id": self.home_id, "event_type": "water_leak",
                "confidence": min(1.0, (1.0 - attenuation) * 3), "zone": "premium",
                "metadata": {"attenuation": round(attenuation, 3)}
            }).execute()

    def get_status(self) -> Dict:
        return {"enabled": True, "baseline": self.baseline}


class StructuralDetector:
    def __init__(self, home_id: str, window_size: int = 1000):
        self.home_id = home_id
        self.window_size = window_size
        self.daily_baselines: Dict[str, float] = {}

    def add_packet(self, amplitude: np.ndarray):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        mean_amp = float(np.mean(np.abs(amplitude)))
        if today not in self.daily_baselines:
            self.daily_baselines[today] = mean_amp
        else:
            self.daily_baselines[today] = self.daily_baselines[today] * 0.99 + mean_amp * 0.01

    def check(self) -> Dict:
        if len(self.daily_baselines) < 7:
            return {"status": "learning", "days_tracked": len(self.daily_baselines), "drift": 0}
        baselines = np.array(list(self.daily_baselines.values()))
        drift = float(np.std(baselines)) / max(float(np.mean(baselines)), 1e-8)
        if drift > 0.05:
            service.table("events").insert({
                "home_id": self.home_id, "event_type": "structural_drift",
                "confidence": min(1.0, drift * 10), "zone": "premium",
                "metadata": {"drift": round(drift, 4), "days": len(self.daily_baselines)}
            }).execute()
        return {"status": "active", "days_tracked": len(self.daily_baselines), "drift": round(drift, 4)}

    def get_status(self) -> Dict:
        return {"enabled": True, "days_tracked": len(self.daily_baselines)}
