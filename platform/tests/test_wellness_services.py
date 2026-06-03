import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from app.services.wellness import BreathingDetector, ApneaDetector, FallDetector
from app.services.baseline import HomeBaseline

def _sine_csi(freq_hz=0.25, duration_s=60, sample_rate=10, n_subcarriers=52, n_tx=3):
    """Generate synthetic CSI amplitude with a known breathing frequency."""
    t = np.linspace(0, duration_s, int(duration_s * sample_rate), endpoint=False)
    breathing = np.sin(2 * np.pi * freq_hz * t) * 0.5 + 1.0
    frames = []
    for i, b in enumerate(breathing):
        frame = np.ones((n_tx, n_subcarriers), dtype=np.float32) * b
        frame += np.random.randn(n_tx, n_subcarriers).astype(np.float32) * 0.05
        frames.append(frame)
    return frames

def _noise_csi(duration_s=60, sample_rate=10, n_subcarriers=52, n_tx=3):
    """Generate synthetic CSI with just noise (no breathing pattern)."""
    frames = []
    for _ in range(int(duration_s * sample_rate)):
        frame = np.random.randn(n_tx, n_subcarriers).astype(np.float32) * 0.3
        frames.append(frame)
    return frames

class TestBreathingDetector:
    def test_detects_normal_breathing(self):
        d = BreathingDetector("test_home")
        frames = _sine_csi(freq_hz=0.25, duration_s=35)  # ~15 BPM
        for f in frames:
            d.add_packet(f)
        result = d.detect()
        assert result["breathing_rate_bpm"] is not None
        assert 10 < result["breathing_rate_bpm"] < 20
        assert result["status"] == "active"
        assert result["confidence"] > 0.5

    def test_detects_slow_breathing(self):
        d = BreathingDetector("test_home")
        frames = _sine_csi(freq_hz=0.15, duration_s=35)  # ~9 BPM
        for f in frames:
            d.add_packet(f)
        result = d.detect()
        assert result["breathing_rate_bpm"] is not None
        assert 5 < result["breathing_rate_bpm"] < 14

    def test_detects_fast_breathing(self):
        d = BreathingDetector("test_home")
        frames = _sine_csi(freq_hz=0.4, duration_s=35)  # ~24 BPM
        for f in frames:
            d.add_packet(f)
        result = d.detect()
        assert result["breathing_rate_bpm"] is not None
        assert 18 < result["breathing_rate_bpm"] < 30

    def test_returns_buffering_insufficient_data(self):
        d = BreathingDetector("test_home")
        frames = _sine_csi(duration_s=10)  # only 10 seconds
        for f in frames:
            d.add_packet(f)
        result = d.detect()
        assert result["status"] == "buffering"
        assert result["breathing_rate_bpm"] is None

    def test_no_crash_on_noise(self):
        d = BreathingDetector("test_home")
        frames = _noise_csi(duration_s=35)
        for f in frames:
            d.add_packet(f)
        result = d.detect()
        assert "breathing_rate_bpm" in result
        assert "status" in result

    def test_returns_empty_buffer_initially(self):
        d = BreathingDetector("test_home")
        result = d.detect()
        assert result["status"] == "buffering"
        assert result["samples"] == 0

    def test_multiple_homes_isolated(self):
        d1 = BreathingDetector("home_a")
        d2 = BreathingDetector("home_b")
        frames = _sine_csi(duration_s=35)
        for f in frames:
            d1.add_packet(f)
        r1 = d1.detect()
        r2 = d2.detect()
        assert r1["breathing_rate_bpm"] is not None
        assert r2["breathing_rate_bpm"] is None


class TestApneaDetector:
    def test_normal_breathing_no_apnea(self):
        d = ApneaDetector("test_home")
        # Normal envelope: 1.0 baseline with small noise
        for _ in range(600):
            sample = 1.0 + np.random.randn() * 0.05
            d.add_envelope_sample(sample)
        result = d.detect_apnea()
        assert result["status"] == "active"
        assert result["ahi"] == 0
        assert result["severity"] == "normal"

    def test_detects_apnea_event(self):
        d = ApneaDetector("test_home")
        # 5 minutes of normal breathing
        for _ in range(300):
            d.add_envelope_sample(1.0 + np.random.randn() * 0.05)
        # 15 seconds of apnea (amplitude drop)
        for _ in range(150):
            d.add_envelope_sample(0.1)
        # More normal breathing
        for _ in range(150):
            d.add_envelope_sample(1.0 + np.random.randn() * 0.05)
        result = d.detect_apnea()
        assert result["total_events"] >= 1
        assert result["apneas"] >= 1
        assert result["ahi"] > 0

    def test_detects_hypopnea(self):
        d = ApneaDetector("test_home")
        for _ in range(300):
            d.add_envelope_sample(1.0 + np.random.randn() * 0.05)
        # Hypopnea: 50% amplitude drop for 15 seconds
        for _ in range(150):
            d.add_envelope_sample(0.5)
        for _ in range(150):
            d.add_envelope_sample(1.0 + np.random.randn() * 0.05)
        result = d.detect_apnea()
        assert result["hypopneas"] >= 1
        assert result["total_events"] >= 1

    def test_not_initialized_with_no_data(self):
        d = ApneaDetector("test_home")
        result = d.detect_apnea()
        assert result["status"] in ("buffering", "not_initialized")

    def test_buffering_with_few_samples(self):
        d = ApneaDetector("test_home")
        for _ in range(50):
            d.add_envelope_sample(1.0)
        result = d.detect_apnea()
        assert result["status"] == "buffering"

    def test_ahi_calculation(self):
        d = ApneaDetector("test_home")
        # 10 minutes of data with 3 apnea events
        for _ in range(180):
            d.add_envelope_sample(1.0)
        for _ in range(100):
            d.add_envelope_sample(0.1)
        for _ in range(100):
            d.add_envelope_sample(1.0)
        for _ in range(100):
            d.add_envelope_sample(0.1)
        for _ in range(100):
            d.add_envelope_sample(1.0)
        result = d.detect_apnea()
        assert result["ahi"] > 0
        # AHI should be (apneas + hypopneas) * 60 / minutes
        expected_ahi = result["total_events"] * 60 / (result.get("minutes_monitored", 1))
        assert abs(result["ahi"] - expected_ahi) < 2.0

    def test_severity_classification(self):
        d = ApneaDetector("test_home")
        # Simulate severe apnea: many events in short period
        for _ in range(300):
            d.add_envelope_sample(1.0)
        for _ in range(200):
            d.add_envelope_sample(0.1)
        for _ in range(200):
            d.add_envelope_sample(1.0)
        result = d.detect_apnea()
        assert result["severity"] in ("mild", "moderate", "severe")


class TestFallDetector:
    def test_no_fall_on_normal_data(self):
        d = FallDetector("test_home")
        for _ in range(40):
            frame = np.random.randn(3, 52).astype(np.float32) * 0.02
            d.add_packet(frame)
        result = d.detect()
        assert result["fall_confidence"] == 0
        assert result["status"] == "normal"

    def test_detects_fall_impulse(self):
        d = FallDetector("test_home")
        # 30 normal frames (fit in buffer of 50)
        for _ in range(30):
            d.add_packet(np.random.randn(3, 52).astype(np.float32) * 0.02)
        # 5 impulse frames (sharp change = fall)
        for _ in range(5):
            d.add_packet(np.random.randn(3, 52).astype(np.float32) * 2.0)
        # 15 stillness frames (post-fall stillness)
        for _ in range(15):
            d.add_packet(np.random.randn(3, 52).astype(np.float32) * 0.01)
        result = d.detect()
        assert result["fall_confidence"] > 0.3
        assert result["status"] in ("fall_detected", "possible_fall")

    def test_returns_learning_initially(self):
        d = FallDetector("test_home")
        result = d.detect()
        assert result["status"] == "learning"

    def test_fall_without_stillness_lower_confidence(self):
        d = FallDetector("test_home")
        for _ in range(30):
            d.add_packet(np.random.randn(3, 52).astype(np.float32) * 0.02)
        for _ in range(5):
            d.add_packet(np.random.randn(3, 52).astype(np.float32) * 2.0)
        for _ in range(15):
            d.add_packet(np.random.randn(3, 52).astype(np.float32) * 0.2)  # no stillness
        result = d.detect()
        assert result["fall_confidence"] > 0


class TestHomeBaseline:
    def test_is_learning_returns_true_during_learning_period(self):
        b = HomeBaseline("test_home")
        assert b.is_learning() is True

    def test_learning_start_is_recent(self):
        b = HomeBaseline("test_home")
        elapsed = (datetime.now(timezone.utc) - b.learning_start).total_seconds()
        assert elapsed < 5

    def test_add_frame_accumulates_samples(self):
        b = HomeBaseline("test_home")
        for i in range(10):
            frame = np.ones((3, 52), dtype=np.float32) * (i + 1)
            b.add_frame(frame)
        assert len(b.samples) == 10

    def test_add_frame_stores_amplitude_data(self):
        b = HomeBaseline("test_home")
        frame = np.full((3, 52), 42.0, dtype=np.float32)
        b.add_frame(frame)
        stored = b.samples[0]
        assert np.allclose(stored, frame)

    def test_is_learning_after_partial_learning_period(self):
        b = HomeBaseline("test_home")
        assert b.is_learning() is True

    def test_get_status_returns_valid_structure(self):
        b = HomeBaseline("test_home")
        s = b.get_status()
        assert s["home_id"] == "test_home"
        assert "learning" in s
        assert "days_remaining" in s
        assert "samples_collected" in s
        assert "baseline_computed" in s
        assert "learning_start" in s
        assert "learning_days" in s
        assert s["learning"] is True
        assert s["baseline_computed"] is False

    def test_get_status_after_adding_frames(self):
        b = HomeBaseline("test_home")
        for _ in range(100):
            b.add_frame(np.random.randn(3, 52).astype(np.float32))
        s = b.get_status()
        assert s["samples_collected"] == 100

    def test_get_baseline_returns_none_during_learning(self):
        b = HomeBaseline("test_home")
        assert b.get_baseline() is None

    def test_get_baseline_returns_none_without_enough_samples(self):
        b = HomeBaseline("test_home", learning_days=1)
        for _ in range(10):
            b.add_frame(np.ones((3, 52), dtype=np.float32))
        bl = b.get_baseline()
        assert bl is None

    def test_is_learning_false_after_learning_days_elapsed(self):
        b = HomeBaseline("test_home", learning_days=0)
        assert b.is_learning() is False
