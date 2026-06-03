import numpy as np
from collections import deque
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta


class HomeBaseline:
    """7-day silent learning period per home before alerts fire."""

    def __init__(self, home_id: str, learning_days: int = 7):
        self.home_id = home_id
        self.learning_days = learning_days
        self.samples = deque(maxlen=864000)
        self.baseline_stats: Optional[Dict] = None
        self.learning_start = datetime.now(timezone.utc)
        self._n_subcarriers = 52
        self._n_antennas = 3

    def add_frame(self, amplitude: np.ndarray):
        self.samples.append(amplitude.copy())

        if not self.is_learning():
            return

        self._check_compute()

    def _check_compute(self):
        samples_needed = self.learning_days * 86400 * 10
        if len(self.samples) >= samples_needed and self.baseline_stats is None:
            stacked = np.stack(list(self.samples))
            self.baseline_stats = {
                "mean": float(np.mean(stacked)),
                "std": float(np.std(stacked)),
                "per_antenna_mean": [float(np.mean(stacked[:, a, :])) for a in range(self._n_antennas)],
                "per_antenna_std": [float(np.std(stacked[:, a, :])) for a in range(self._n_antennas)],
                "per_subcarrier_mean": [float(np.mean(stacked[:, :, s])) for s in range(self._n_subcarriers)],
                "per_subcarrier_std": [float(np.std(stacked[:, :, s])) for s in range(self._n_subcarriers)],
                "samples": len(self.samples),
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }

    def is_learning(self) -> bool:
        if self.baseline_stats is not None:
            return False
        elapsed = (datetime.now(timezone.utc) - self.learning_start).total_seconds()
        return elapsed < self.learning_days * 86400

    def get_baseline(self) -> Optional[Dict]:
        return self.baseline_stats

    def get_status(self) -> Dict:
        elapsed = (datetime.now(timezone.utc) - self.learning_start).total_seconds()
        remaining = max(0, self.learning_days * 86400 - elapsed)
        return {
            "home_id": self.home_id,
            "learning": self.is_learning(),
            "days_remaining": round(remaining / 86400, 1),
            "samples_collected": len(self.samples),
            "baseline_computed": self.baseline_stats is not None,
            "learning_start": self.learning_start.isoformat(),
            "learning_days": self.learning_days,
        }


baselines: Dict[str, HomeBaseline] = {}
