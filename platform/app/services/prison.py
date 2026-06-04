from typing import Dict, List
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import numpy as np

RIOT_WINDOW_MINUTES = 10
RIOT_WEIGHTS = {
    "hr_deviation": 0.40,
    "crowding": 0.25,
    "gait_anomaly": 0.20,
    "movement_amplitude": 0.15,
}

class BlockState:
    def __init__(self, block_id: str, capacity: int = 50):
        self.block_id = block_id
        self.capacity = capacity
        self.hr_readings: List[float] = []
        self.occupancy: int = 0
        self.crowded_cells: int = 0
        self.pacing_count: int = 0
        self.movement_amplitude: float = 0.5
        self.baseline_hr: float = 70.0
        self.baseline_hr_set = False
        self.last_update = datetime.now(timezone.utc)
        self.alert_thresholds = {
            "hr_spike": 20,
            "hr_absolute": 90,
            "crowding": 5,
            "riot_probability": 0.60,
            "tamper_sensitivity": "medium",
            "offline_alert_minutes": 5,
        }

    def ingest_hr(self, hr: float):
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=RIOT_WINDOW_MINUTES)
        self.hr_readings = [r for r in self.hr_readings if r[0] > window_start.timestamp()]
        self.hr_readings.append((now.timestamp(), hr))
        if not self.baseline_hr_set and len(self.hr_readings) > 10:
            self.baseline_hr = np.mean([r[1] for r in self.hr_readings])
            self.baseline_hr_set = True
        self.last_update = now

    def ingest_occupancy(self, count: int, crowded_cells: int, pacing: int, amplitude: float):
        self.occupancy = count
        self.crowded_cells = crowded_cells
        self.pacing_count = pacing
        self.movement_amplitude = amplitude
        self.last_update = datetime.now(timezone.utc)

    def set_threshold(self, key: str, value):
        if key in self.alert_thresholds:
            self.alert_thresholds[key] = value

    def compute_riot_probability(self) -> dict:
        if len(self.hr_readings) < 5 or not self.baseline_hr_set:
            return {"probability": 0.0, "status": "buffering", "factors": {}}

        avg_hr = np.mean([r[1] for r in self.hr_readings[-20:]])
        hr_dev = (avg_hr - self.baseline_hr) / self.baseline_hr
        hr_score = min(1.0, max(0, hr_dev * 3))

        crowding_ratio = self.crowded_cells / max(1, self.occupancy / 4)
        crowding_score = min(1.0, crowding_ratio * 2)

        pacing_ratio = self.pacing_count / max(1, self.occupancy)
        gait_score = min(1.0, pacing_ratio * 3)

        amp_score = min(1.0, self.movement_amplitude * 2)

        raw_score = (
            hr_score * RIOT_WEIGHTS["hr_deviation"]
            + crowding_score * RIOT_WEIGHTS["crowding"]
            + gait_score * RIOT_WEIGHTS["gait_anomaly"]
            + amp_score * RIOT_WEIGHTS["movement_amplitude"]
        )

        probability = round(raw_score, 3)
        threshold = self.alert_thresholds["riot_probability"]
        alert = probability >= threshold
        severity = "critical" if probability >= 0.80 else "high" if probability >= 0.60 else "medium" if probability >= 0.40 else "low"

        return {
            "probability": probability,
            "status": "alert" if alert else "monitoring",
            "severity": severity,
            "avg_hr": round(avg_hr, 1),
            "baseline_hr": self.baseline_hr,
            "occupancy": self.occupancy,
            "crowded_cells": self.crowded_cells,
            "pacing_count": self.pacing_count,
            "factors": {
                "hr_score": round(hr_score, 3),
                "crowding_score": round(crowding_score, 3),
                "gait_score": round(gait_score, 3),
                "amplitude_score": round(amp_score, 3),
            },
            "thresholds": self.alert_thresholds,
        }


class PrisonEngine:
    def __init__(self):
        self.blocks: Dict[str, BlockState] = {}

    def get_block(self, block_id: str, capacity: int = 50) -> BlockState:
        if block_id not in self.blocks:
            self.blocks[block_id] = BlockState(block_id, capacity)
        return self.blocks[block_id]

    def get_all_status(self) -> list:
        return [b.compute_riot_probability() for b in self.blocks.values()]

    def set_global_threshold(self, key: str, value):
        for block in self.blocks.values():
            block.set_threshold(key, value)

prison_engine = PrisonEngine()
