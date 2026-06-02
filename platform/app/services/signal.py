import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timezone
import json

class CsiProcessor:
    def __init__(self, home_id: str, window_size: int = 100):
        self.home_id = home_id
        self.window_size = window_size
        self.baseline_mean: Optional[np.ndarray] = None
        self.baseline_std: Optional[np.ndarray] = None
        self.history: List[np.ndarray] = []
        self.confidence_thresholds = {
            "alert": 0.92,
            "dashboard": 0.80,
            "log": 0.60,
        }

    def update_baseline(self, amplitude: np.ndarray):
        self.history.append(amplitude)
        if len(self.history) > self.window_size:
            self.history.pop(0)
        if len(self.history) >= 20:
            stacked = np.stack(self.history)
            self.baseline_mean = np.mean(stacked, axis=0)
            self.baseline_std = np.std(stacked, axis=0) + 1e-8

    def compute_confidence(self, amplitude: np.ndarray) -> float:
        if self.baseline_mean is None or self.baseline_std is None:
            return 0.0
        z_scores = np.abs((amplitude - self.baseline_mean) / self.baseline_std)
        max_z = float(np.max(z_scores))
        n_anomalous = int(np.sum(z_scores > 2.5))
        n_total = int(z_scores.size)
        anomaly_ratio = n_anomalous / max(n_total, 1)
        spatial_spread = float(np.std(z_scores))
        confidence = min(1.0, anomaly_ratio * 0.6 + (max_z / 8.0) * 0.3 + spatial_spread * 0.1)
        return round(max(0.0, confidence), 4)

    def classify(self, confidence: float) -> str:
        if confidence >= self.confidence_thresholds["alert"]:
            return "intrusion"
        elif confidence >= self.confidence_thresholds["dashboard"]:
            return "motion"
        elif confidence >= self.confidence_thresholds["log"]:
            return "motion"
        return "motion"

    def process_csi(self, csi_bytes: bytes) -> Dict:
        n_subcarriers = 52
        n_antennas = 3
        expected_values = n_antennas * n_subcarriers
        data = np.frombuffer(csi_bytes, dtype=np.float32)
        if data.size < expected_values:
            return {"confidence": 0.0, "event_type": "motion", "is_anomaly": False}
        amplitude = data.reshape(n_antennas, n_subcarriers)
        self.update_baseline(amplitude)
        confidence = self.compute_confidence(amplitude)
        event_type = self.classify(confidence)
        return {
            "confidence": confidence,
            "event_type": event_type,
            "is_anomaly": event_type == "intrusion",
        }

processors: Dict[str, CsiProcessor] = {}
