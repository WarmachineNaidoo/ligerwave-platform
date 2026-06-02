import numpy as np
from scipy import signal as sp_signal
from typing import Optional, Dict

class BreathingRateEstimator:
    def __init__(self, fs: float = 10.0):
        self.fs = fs
        self.buffer = []
        self.window_seconds = 30

    def estimate(self, amplitude: np.ndarray) -> Optional[Dict]:
        self.buffer.append(amplitude)
        if len(self.buffer) < self.fs * self.window_seconds:
            return None
        self.buffer = self.buffer[-int(self.fs * self.window_seconds):]
        stacked = np.stack(self.buffer)
        phase_signal = np.angle(stacked).mean(axis=1)
        freqs, psd = sp_signal.welch(phase_signal, fs=self.fs, nperseg=min(64, len(phase_signal)))
        breathing_range = (0.1, 0.5)
        mask = (freqs >= breathing_range[0]) & (freqs <= breathing_range[1])
        if not np.any(mask):
            return None
        peak_idx = np.argmax(psd[mask])
        peak_freq = freqs[mask][peak_idx]
        breathing_rate = peak_freq * 60
        confidence = min(1.0, psd[mask][peak_idx] / np.mean(psd) * 0.1)
        return {
            "breathing_rate_bpm": round(breathing_rate, 1),
            "confidence": round(confidence, 4),
        }

estimators = {}
