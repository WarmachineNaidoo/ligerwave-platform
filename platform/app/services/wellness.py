import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import deque
from scipy import signal as scipy_signal
from app.database import service

class BreathingDetector:
    def __init__(self, home_id: str, window_seconds: int = 30, sample_rate_hz: float = 10):
        self.home_id = home_id
        self.window_size = int(window_seconds * sample_rate_hz)
        self.sample_rate = sample_rate_hz
        self.buffer: deque = deque(maxlen=self.window_size)
        self.last_rate: Optional[float] = None
        self.last_confidence: float = 0.0
        # For apnea: keep a longer envelope for detecting cessations
        self.envelope: deque = deque(maxlen=300)

    def add_packet(self, amplitude: np.ndarray):
        raveled = amplitude.ravel()
        self.buffer.append(raveled)
        if len(self.buffer) >= 5:
            # Store the mean amplitude of the PC1 as a breathing envelope proxy
            stacked = np.stack(list(self.buffer)[-5:])
            mean_amp = float(np.mean(np.abs(stacked - np.mean(stacked, axis=0))))
            self.envelope.append(mean_amp)

    def detect(self) -> Dict:
        if len(self.buffer) < self.window_size * 0.5:
            return {"breathing_rate_bpm": None, "confidence": 0, "status": "buffering", "samples": len(self.buffer)}

        stacked = np.stack(list(self.buffer))
        if stacked.ndim != 2:
            return {"breathing_rate_bpm": None, "confidence": 0, "status": "error", "samples": len(self.buffer)}
        n_samples, n_features = stacked.shape

        stacked_centered = stacked - np.mean(stacked, axis=0)
        cov = (stacked_centered.T @ stacked_centered) / max(n_samples - 1, 1)

        try:
            eigvals, eigvecs = np.linalg.eigh(cov)
            pc1 = stacked_centered @ eigvecs[:, -1]
        except np.linalg.LinAlgError:
            pc1 = stacked.mean(axis=1)

        window = np.hamming(len(pc1))
        pc1_windowed = pc1 * window

        nfft = int(2 ** np.ceil(np.log2(len(pc1_windowed))))
        freqs = np.fft.rfftfreq(nfft, 1.0 / self.sample_rate)
        spectrum = np.abs(np.fft.rfft(pc1_windowed, n=nfft))

        valid = (freqs >= 0.1) & (freqs <= 0.5)
        if not np.any(valid):
            return {"breathing_rate_bpm": None, "confidence": 0, "status": "no_signal"}

        peak_idx = np.argmax(spectrum * valid)
        peak_freq = freqs[peak_idx]
        breathing_rate = peak_freq * 60.0

        total_power = np.sum(spectrum[valid])
        peak_power = spectrum[peak_idx]
        confidence = min(1.0, peak_power / max(total_power * 0.15, 1e-10))
        confidence = max(0.0, min(1.0, confidence))

        self.last_rate = breathing_rate
        self.last_confidence = confidence

        return {
            "breathing_rate_bpm": round(breathing_rate, 1),
            "confidence": round(confidence, 3),
            "status": "active",
            "samples": n_samples,
            "peak_freq_hz": round(peak_freq, 3),
            "total_power": round(float(total_power), 4),
        }


class ApneaDetector:
    """Detects sleep apnea events from breathing envelope.
    
    Apnea = breathing amplitude drops below threshold for >= 10 seconds.
    Hypopnea = amplitude drops by >= 30% for >= 10 seconds.
    AHI = (apneas + hypopneas) * 60 / total_sleep_minutes.
    """
    
    def __init__(self, home_id: str, sample_rate_hz: float = 2.0):
        self.home_id = home_id
        self.sample_rate = sample_rate_hz
        self.envelope: deque = deque(maxlen=1800)  # 15 min at 2Hz
        self.baseline: Optional[float] = None
        self.baseline_samples: int = 0
        self.apnea_events: List[Dict] = []
        self.last_apnea_end: Optional[float] = None

    def add_envelope_sample(self, amplitude: float):
        self.envelope.append(amplitude)
        if self.baseline is None or self.baseline_samples < 300:
            if self.baseline is None:
                self.baseline = amplitude
            else:
                self.baseline = self.baseline * 0.99 + amplitude * 0.01
            self.baseline_samples += 1

    def detect_apnea(self) -> Dict:
        """Scan envelope for apnea/hypopnea events. Returns latest AHI."""
        if len(self.envelope) < 60 or self.baseline is None or self.baseline < 1e-8:
            return {"ahi": 0, "apneas": 0, "hypopneas": 0, "total_events": 0, "status": "buffering", "minutes_monitored": 0}

        arr = np.array(list(self.envelope))
        minutes = len(arr) / (self.sample_rate * 60)

        # Detect drops: normalize by baseline
        norm = arr / self.baseline

        # Find segments below apnea threshold (20% of baseline)
        apnea_threshold = 0.2
        hypopnea_threshold = 0.7

        below_apnea = norm < apnea_threshold
        below_hypopnea = (norm >= apnea_threshold) & (norm < hypopnea_threshold)

        # Find contiguous segments of >= 10 seconds
        min_apnea_samples = int(10 * self.sample_rate)

        new_apneas = 0
        new_hypopneas = 0
        in_event = False
        event_start = None
        event_type = None

        for i in range(len(arr)):
            is_apnea = bool(below_apnea[i])
            is_hypopnea = bool(below_hypopnea[i])

            if is_apnea or is_hypopnea:
                if not in_event:
                    in_event = True
                    event_start = i
                    event_type = "apnea" if is_apnea else "hypopnea"
            else:
                if in_event and event_start is not None:
                    duration = (i - event_start) / self.sample_rate
                    if duration >= 10:
                        if event_type == "apnea":
                            new_apneas += 1
                            self.apnea_events.append({
                                "type": "apnea",
                                "start_sample": event_start,
                                "duration_seconds": round(duration, 1),
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                        else:
                            new_hypopneas += 1
                            self.apnea_events.append({
                                "type": "hypopnea",
                                "start_sample": event_start,
                                "duration_seconds": round(duration, 1),
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                in_event = False
                event_start = None

        total = len([e for e in self.apnea_events if e.get("timestamp", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))])
        ahi = round(total * 60 / max(minutes, 1), 1)

        severity = "normal"
        if ahi >= 30:
            severity = "severe"
        elif ahi >= 15:
            severity = "moderate"
        elif ahi >= 5:
            severity = "mild"

        return {
            "ahi": ahi,
            "apneas": len([e for e in self.apnea_events if e.get("type") == "apnea"]),
            "hypopneas": len([e for e in self.apnea_events if e.get("type") == "hypopnea"]),
            "total_events": total,
            "severity": severity,
            "status": "active",
            "minutes_monitored": round(minutes, 1),
            "baseline_amplitude": round(float(self.baseline), 4),
        }


class FallDetector:
    def __init__(self, home_id: str, window_size: int = 50, pre_samples: int = 10, post_samples: int = 20):
        self.home_id = home_id
        self.window_size = window_size
        self.pre_samples = pre_samples
        self.post_samples = post_samples
        self.buffer: deque = deque(maxlen=window_size)
        self.last_fall_confidence: float = 0.0
        self.baseline_mean: Optional[np.ndarray] = None

    def add_packet(self, amplitude: np.ndarray):
        self.buffer.append(amplitude.ravel())

    def detect(self) -> Dict:
        if len(self.buffer) < 20:
            return {"fall_confidence": 0, "status": "learning", "samples": len(self.buffer)}

        stacked = np.stack(list(self.buffer))

        diffs = np.abs(np.diff(stacked, axis=0))
        frame_scores = np.mean(diffs, axis=1)

        if self.baseline_mean is None:
            baseline_frames = frame_scores[:15]
            self.baseline_mean = np.mean(baseline_frames) + 1e-8

        z_scores = (frame_scores - self.baseline_mean) / max(self.baseline_mean * 0.5, 1e-8)

        impulse_idx = int(np.argmax(z_scores))
        impulse_strength = float(z_scores[impulse_idx])

        if impulse_strength < 5.0:
            self.last_fall_confidence = 0
            return {"fall_confidence": 0, "status": "normal", "max_z": round(impulse_strength, 1)}

        post_impulse = frame_scores[impulse_idx:impulse_idx + self.post_samples]
        if len(post_impulse) < 3:
            stillness = 1.0
        else:
            stillness = 1.0 - min(1.0, np.std(post_impulse) / max(self.baseline_mean, 1e-8))

        fall_score = min(1.0, (impulse_strength / 15.0) * 0.6 + stillness * 0.4)
        self.last_fall_confidence = fall_score

        return {
            "fall_confidence": round(fall_score, 3),
            "status": "fall_detected" if fall_score > 0.6 else "possible_fall",
            "impulse_strength": round(impulse_strength, 1),
            "stillness": round(stillness, 3),
            "impulse_index": int(impulse_idx),
        }


breathing_detectors: Dict[str, BreathingDetector] = {}
fall_detectors: Dict[str, FallDetector] = {}
apnea_detectors: Dict[str, ApneaDetector] = {}
