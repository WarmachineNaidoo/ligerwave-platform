"""
Cross-Validation Engine: CSI + mmWave + Door Sensor Correlation

Reduces false alarms by requiring confirmation from 2+ sensor modalities
before raising the confidence level. The engine subscribes to events from
all sensor sources and produces a fused confidence score.

Sensor reliability weights:
  - CSI only (no other sensor): base weight 0.6
  - CSI + mmWave presence: weight 0.9 (mmWave sees stationary people)
  - CSI + 433 MHz door sensor: weight 0.85 (door opened + CSI motion)
  - CSI + mmWave + door: weight 0.98 (all three agree)
  - mmWave only (no CSI): weight 0.4 (can't identify, only presence)
"""

import time
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timezone, timedelta
from app.database import service

# Confidence tiers
CONFIDENCE_MAP = {
    "none":        0.0,
    "csi_only":    0.60,
    "mmwave_only": 0.40,
    "door_only":   0.50,
    "csi_mmwave":  0.90,
    "csi_door":    0.85,
    "mmwave_door": 0.75,
    "all_three":   0.98,
}

# Time window (seconds) to consider events as correlated
CORRELATION_WINDOW = 15.0


class CrossValidator:
    """Correlates events from CSI, mmWave, and 433 MHz sensors."""

    def __init__(self, home_id: str):
        self.home_id = home_id
        self._csi_events: deque = deque(maxlen=50)
        self._mmwave_events: deque = deque(maxlen=50)
        self._door_events: deque = deque(maxlen=50)
        self._last_fused: Optional[float] = None
        self._last_decision: str = "none"

    def ingest_csi(self, event_type: str, confidence: float, zone: str = "default"):
        """Receive a CSI-detected event."""
        self._csi_events.append({
            "ts": time.time(), "type": event_type,
            "confidence": confidence, "zone": zone
        })
        return self._fuse()

    def ingest_mmwave(self, present: bool, distance_cm: int = 0):
        """Receive an mmWave presence reading."""
        if present:
            self._mmwave_events.append({
                "ts": time.time(), "distance_cm": distance_cm
            })
        return self._fuse()

    def ingest_door(self, state: str):
        """Receive a door open/close event."""
        self._door_events.append({
            "ts": time.time(), "state": state
        })
        return self._fuse()

    def _recent(self, buf: deque, window: float = CORRELATION_WINDOW) -> bool:
        """Check if there's a recent event in the buffer."""
        now = time.time()
        for e in buf:
            if now - e["ts"] <= window:
                return True
        return False

    def _fuse(self) -> Dict:
        """Fuse all sensor inputs into a single decision."""
        now = time.time()
        has_csi = self._recent(self._csi_events)
        has_mmwave = self._recent(self._mmwave_events)
        has_door = self._recent(self._door_events)

        # Determine sensor combination
        combo = 0
        if has_csi: combo += 1
        if has_mmwave: combo += 2
        if has_door: combo += 4

        combo_map = {
            1: "csi_only", 2: "mmwave_only", 4: "door_only",
            3: "csi_mmwave", 5: "csi_door", 6: "mmwave_door",
            7: "all_three",
        }
        key = combo_map.get(combo, "none")
        confidence = CONFIDENCE_MAP.get(key, 0.0)

        # Get the best CSI confidence for details
        best_csi = 0.0
        best_type = "motion"
        for e in self._csi_events:
            if now - e["ts"] <= CORRELATION_WINDOW and e["confidence"] > best_csi:
                best_csi = e["confidence"]
                best_type = e["type"]

        # Fused confidence = cross-validation multiplier * base CSI confidence
        fused = min(1.0, confidence * max(best_csi, 0.5)) if has_csi else confidence

        should_alert = fused >= 0.8
        decision = "alert" if should_alert else "log"

        self._last_fused = fused
        self._last_decision = decision

        return {
            "fused_confidence": round(fused, 3),
            "sensors": key,
            "decision": decision,
            "should_alert": should_alert,
            "event_type": best_type,
            "csi": has_csi,
            "mmwave": has_mmwave,
            "door": has_door,
            "correlation_window_s": CORRELATION_WINDOW,
        }

    def should_alert(self, min_confidence: float = 0.8) -> bool:
        """Returns True if fused confidence exceeds threshold."""
        result = self._fuse()
        return result["should_alert"] and result["fused_confidence"] >= min_confidence

    def get_status(self) -> Dict:
        return {
            "csi_buffered": len(self._csi_events),
            "mmwave_buffered": len(self._mmwave_events),
            "door_buffered": len(self._door_events),
            "last_fused": self._last_fused,
            "last_decision": self._last_decision,
        }


# Global instances
_validators: Dict[str, CrossValidator] = {}


def get_validator(home_id: str) -> CrossValidator:
    """Get or create a CrossValidator for a home."""
    if home_id not in _validators:
        _validators[home_id] = CrossValidator(home_id)
    return _validators[home_id]


def validate_event(home_id: str, event_type: str, confidence: float, zone: str = "default") -> Dict:
    """Entry point: feed a CSI event through cross-validation and get adjusted confidence."""
    v = get_validator(home_id)
    return v.ingest_csi(event_type, confidence, zone)
