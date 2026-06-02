import numpy as np
from typing import List, Dict
from datetime import datetime, timezone
from uuid import uuid4

class CsiSimulator:
    def __init__(self, home_id: str):
        self.home_id = home_id
        self.baseline = self._generate_baseline()
        self.armed = True

    def _generate_baseline(self, subcarriers: int = 52, num_antennas: int = 3):
        return np.random.randn(num_antennas, subcarriers) + 1j * np.random.randn(num_antennas, subcarriers)

    def simulate_packet(self, intrusion: bool = False) -> Dict:
        now = datetime.now(timezone.utc)
        noise = 0.05 * (np.random.randn(3, 52) + 1j * np.random.randn(3, 52))
        if intrusion:
            signal = 0.3 * (np.random.randn(3, 52) + 1j * np.random.randn(3, 52))
            amplitude = np.abs(self.baseline + signal + noise)
            label = "intrusion"
            confidence = min(1.0, max(0.0, 0.50 + 0.10 * np.random.randn()))
        else:
            amplitude = np.abs(self.baseline + noise)
            label = "motion" if np.random.random() < 0.05 else "normal"
            confidence = 0.0

        csi_bytes = amplitude.astype(np.float32).tobytes()

        return {
            "home_id": self.home_id,
            "event_type": label,
            "confidence": round(confidence, 4),
            "csi_data_b64": csi_bytes.hex(),
            "csi_bytes": len(csi_bytes),
            "timestamp": now.isoformat(),
            "zone": "living_room" if intrusion else None,
            "zone_path": ["entrance", "living_room"] if intrusion else None
        }

simulators: Dict[str, CsiSimulator] = {}
