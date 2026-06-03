#!/usr/bin/env python3
"""
Ligerwave Router CSI Agent v0.1
OpenWrt ath9k/nexmon CSI capture → HTTPS streaming
"""

import argparse
import asyncio
import binascii
import hashlib
import json
import logging
import os
import signal
import socket
import struct
import subprocess
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import numpy as np

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    from uci import UCI  # OpenWrt python3-uci
except ImportError:
    UCI = None

logger = logging.getLogger("ligerwave-agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CONFIG_PATH = "/etc/config/ligerwave"
BACKUP_PATH = "/etc/config/ligerwave.bak"
PID_FILE = "/var/run/ligerwave-agent.pid"
DEFAULT_API_URL = "https://ligerwave.tech/devices/events"
CSI_PIPE = "/tmp/nexmon_csi"
ATH9K_CSI_GLOB = "/sys/kernel/debug/ieee80211/phy*/netdev:*/stations/*/csi"
N_SUBCARRIERS = 52
N_ANTENNAS = 3
FRAME_BYTES = N_ANTENNAS * N_SUBCARRIERS * 2 * 4  # 3×52×2 (I/Q) × float32
PUSH_INTERVAL_S = 0.1  # 100ms
MAX_RETRIES = 10
BASE_DELAY_S = 1.0
MAX_DELAY_S = 60.0


class CsiFrame:
    __slots__ = ("tsf", "rssi", "noise", "csi", "antenna")

    def __init__(self, tsf: int, rssi: float, noise: float, csi: np.ndarray, antenna: int):
        self.tsf = tsf
        self.rssi = rssi
        self.noise = noise
        self.csi = csi
        self.antenna = antenna


@dataclass
class AgentConfig:
    gateway_id: str = field(default_factory=lambda: f"router-{uuid.uuid4().hex[:8]}")
    home_id: str = ""
    api_token: str = ""
    api_url: str = DEFAULT_API_URL
    source: str = "ath9k"  # ath9k or nexmon
    iface: str = "wlan0"
    phy: str = "phy0"
    ca_path: str = "/etc/ssl/certs"


def load_config() -> AgentConfig:
    cfg = AgentConfig()
    if UCI and os.path.exists(CONFIG_PATH):
        try:
            u = UCI()
            u.load("ligerwave")
            cfg.gateway_id = u.get("ligerwave", "agent", "gateway_id") or cfg.gateway_id
            cfg.home_id = u.get("ligerwave", "agent", "home_id") or ""
            cfg.api_token = u.get("ligerwave", "agent", "api_token") or ""
            cfg.api_url = u.get("ligerwave", "agent", "api_url") or DEFAULT_API_URL
            cfg.source = u.get("ligerwave", "agent", "source") or "ath9k"
            cfg.iface = u.get("ligerwave", "agent", "interface") or "wlan0"
        except Exception as exc:
            logger.warning("uci load failed: %s", exc)
    return cfg


def save_config(cfg: AgentConfig):
    if not UCI:
        # Flat file fallback
        data = {k: v for k, v in cfg.__dict__.items() if v}
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f)
        return
    try:
        u = UCI()
        u.set("ligerwave", "agent", "gateway_id", cfg.gateway_id)
        u.set("ligerwave", "agent", "home_id", cfg.home_id)
        u.set("ligerwave", "agent", "api_token", cfg.api_token)
        u.set("ligerwave", "agent", "api_url", cfg.api_url)
        u.set("ligerwave", "agent", "source", cfg.source)
        u.set("ligerwave", "agent", "interface", cfg.iface)
        u.save("ligerwave")
        u.commit("ligerwave")
    except Exception as exc:
        logger.error("uci save failed: %s", exc)


class CsiPipeline:
    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.baseline_mean: Optional[np.ndarray] = None
        self.baseline_std: Optional[np.ndarray] = None
        self.history: Deque[np.ndarray] = deque(maxlen=100)
        self.running = True
        self.session: Optional[aiohttp.ClientSession] = None
        self.batch: List[Dict] = []

    def update_baseline(self, amplitude: np.ndarray):
        self.history.append(amplitude)
        if len(self.history) >= 20:
            stacked = np.stack(list(self.history))
            self.baseline_mean = np.mean(stacked, axis=0)
            self.baseline_std = np.std(stacked, axis=0) + 1e-8

    def compute_confidence(self, amplitude: np.ndarray) -> float:
        if self.baseline_mean is None or self.baseline_std is None:
            return 0.0
        z = np.abs((amplitude - self.baseline_mean) / self.baseline_std)
        max_z = float(np.max(z))
        n_anom = int(np.sum(z > 2.5))
        ratio = n_anom / max(z.size, 1)
        spread = float(np.std(z))
        return round(min(1.0, max(0.0, ratio * 0.6 + (max_z / 8.0) * 0.3 + spread * 0.1)), 4)

    def process_frame(self, frame: CsiFrame) -> Tuple[np.ndarray, float]:
        amplitude = np.abs(frame.csi)
        self.update_baseline(amplitude)
        confidence = self.compute_confidence(amplitude)
        return amplitude, confidence

    def parse_ath9k_csi(self, raw: bytes) -> Optional[CsiFrame]:
        # ath9k CSI debugfs format: TSF(8) + RSSI(4) + noise(4) + num_tones(4) +
        # data[3][52][2] as int16
        hdr_size = 20
        if len(raw) < hdr_size + FRAME_BYTES // 2:
            return None
        tsf = struct.unpack("<Q", raw[:8])[0]
        rssi = struct.unpack("<f", raw[8:12])[0]
        noise = struct.unpack("<f", raw[12:16])[0]
        # CSI data as int16 real/imag pairs
        csi_raw = np.frombuffer(raw[hdr_size:], dtype=np.int16)
        expected = N_ANTENNAS * N_SUBCARRIERS * 2
        if csi_raw.size < expected:
            return None
        csi_raw = csi_raw[:expected]
        csi_complex = csi_raw[0::2].astype(np.float32) + 1j * csi_raw[1::2].astype(np.float32)
        csi_complex = csi_complex.reshape(N_ANTENNAS, N_SUBCARRIERS)
        return CsiFrame(tsf=tsf, rssi=rssi, noise=noise, csi=csi_complex, antenna=0)

    def parse_nexmon_csi(self, raw: bytes) -> Optional[CsiFrame]:
        # Nexmon CSI binary format:
        # magic(1) + frame_control(2) + duration(2) + DA(6) + SA(6) + BSSID(6) +
        # seq(2) + timestamp(4) + core(1) + rssi(1) + payload(0) + csi_data_len(2) + csi_data(N)
        if len(raw) < 32:
            return None
        if raw[0] != 0xFE:
            return None
        rssi = -raw[27]
        csi_len = struct.unpack("<H", raw[30:32])[0]
        csi_start = 32
        if len(raw) < csi_start + csi_len:
            return None
        csi_raw = np.frombuffer(raw[csi_start:csi_start + csi_len], dtype=np.int16)
        expected = N_ANTENNAS * N_SUBCARRIERS * 2
        if csi_raw.size < expected:
            return None
        csi_raw = csi_raw[:expected]
        csi_complex = csi_raw[0::2].astype(np.float32) + 1j * csi_raw[1::2].astype(np.float32)
        csi_complex = csi_complex.reshape(N_ANTENNAS, N_SUBCARRIERS)
        tsf = struct.unpack("<I", raw[22:26])[0]
        return CsiFrame(tsf=tsf, rssi=float(rssi), noise=0.0, csi=csi_complex, antenna=raw[26])

    async def push_batch(self):
        if not self.batch:
            return
        events = self.batch
        self.batch = []

        # Combine multiple frames into single event with hex
        csi_bytes = b"".join(e["csi_bytes"] for e in events)
        avg_confidence = max(e["confidence"] for e in events)
        max_event_type = max(events, key=lambda e: e["confidence"])["event_type"]

        payload = {
            "gateway_id": self.cfg.gateway_id,
            "home_id": self.cfg.home_id,
            "event_type": max_event_type,
            "confidence": avg_confidence,
            "zone": "router",
            "zone_path": ["router"],
            "csi_data_hex": binascii.hexlify(csi_bytes).decode("ascii"),
        }

        retries = 0
        delay = BASE_DELAY_S
        while self.running and retries < MAX_RETRIES:
            try:
                async with self.session.post(
                    self.cfg.api_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.cfg.api_token}",
                        "Content-Type": "application/json",
                    },
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status < 500:
                        logger.debug("pushed %d frames, status=%d", len(events), resp.status)
                        return
                    text = await resp.text()
                    logger.warning("push failed %d: %s", resp.status, text[:200])
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.warning("push error: %s", exc)
            except Exception as exc:
                logger.error("push unexpected: %s", exc)

            retries += 1
            logger.info("backoff %.1fs (retry %d/%d)", delay, retries, MAX_RETRIES)
            await asyncio.sleep(delay)
            delay = min(delay * 2, MAX_DELAY_S)

    async def reader_ath9k(self):
        import glob
        while self.running:
            paths = glob.glob(ATH9K_CSI_GLOB)
            if not paths:
                logger.warning("no ath9k CSI files found at %s", ATH9K_CSI_GLOB)
                await asyncio.sleep(5)
                continue
            for path in paths:
                try:
                    with open(path, "rb") as f:
                        f.seek(0, os.SEEK_END)
                        while self.running:
                            line = f.read()
                            if line:
                                for i in range(0, len(line), FRAME_BYTES // 2):
                                    chunk = line[i:i + FRAME_BYTES // 2]
                                    frame = self.parse_ath9k_csi(chunk)
                                    if frame:
                                        amp, conf = self.process_frame(frame)
                                        etype = "intrusion" if conf >= 0.92 else "motion" if conf >= 0.60 else "normal"
                                        self.batch.append({
                                            "csi_bytes": chunk,
                                            "confidence": conf,
                                            "event_type": etype,
                                        })
                            await asyncio.sleep(0.01)
                except (IOError, OSError) as exc:
                    logger.error("ath9k read error %s: %s", path, exc)
                    await asyncio.sleep(2)

    async def reader_nexmon(self):
        while self.running:
            try:
                if not os.path.exists(CSI_PIPE):
                    logger.warning("nexmon pipe %s not found, waiting...", CSI_PIPE)
                    await asyncio.sleep(5)
                    continue
                with open(CSI_PIPE, "rb") as f:
                    while self.running:
                        # Read 4-byte length prefix
                        hdr = f.read(4)
                        if not hdr or len(hdr) < 4:
                            await asyncio.sleep(0.01)
                            continue
                        pkt_len = struct.unpack("<I", hdr)[0]
                        pkt = f.read(pkt_len)
                        if len(pkt) < pkt_len:
                            continue
                        frame = self.parse_nexmon_csi(pkt)
                        if frame:
                            amp, conf = self.process_frame(frame)
                            etype = "intrusion" if conf >= 0.92 else "motion" if conf >= 0.60 else "normal"
                            self.batch.append({
                                "csi_bytes": pkt,
                                "confidence": conf,
                                "event_type": etype,
                            })
            except (IOError, OSError) as exc:
                logger.error("nexmon read error: %s", exc)
                await asyncio.sleep(2)

    async def pusher(self):
        while self.running:
            await asyncio.sleep(PUSH_INTERVAL_S)
            if self.batch and self.session and self.cfg.api_token:
                await self.push_batch()

    async def run(self):
        if aiohttp is None:
            logger.error("aiohttp not installed: pip install aiohttp")
            sys.exit(1)
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self.cfg.ca_path if os.path.exists(self.cfg.ca_path) else True)
        )
        reader = self.reader_ath9k() if self.cfg.source == "ath9k" else self.reader_nexmon()
        await asyncio.gather(reader, self.pusher())

    async def shutdown(self):
        self.running = False
        if self.session:
            await self.session.close()


def cmd_pair():
    """Generate pairing URL and print QR code."""
    from agent.pairing import generate_pairing_qr

    cfg = load_config()
    cfg.home_id = input("Enter home ID from dashboard: ").strip()
    cfg.api_token = input("Enter API token from dashboard: ").strip()
    save_config(cfg)
    generate_pairing_qr(cfg.gateway_id)
    print(f"\nGateway ID: {cfg.gateway_id}")
    print(f"Home ID: {cfg.home_id}")
    print("Config saved to", CONFIG_PATH)


def cmd_daemon():
    cfg = load_config()
    if not cfg.api_token:
        logger.error("Not paired. Run --pair first.")
        sys.exit(1)
    if not cfg.home_id:
        logger.error("No home_id configured. Run --pair first.")
        sys.exit(1)

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    pipeline = CsiPipeline(cfg)

    def _shutdown():
        logger.info("shutting down...")
        asyncio.run_coroutine_threadsafe(pipeline.shutdown(), asyncio.get_event_loop())

    signal.signal(signal.SIGTERM, lambda s, f: _shutdown())
    signal.signal(signal.SIGINT, lambda s, f: _shutdown())

    try:
        asyncio.run(pipeline.run())
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("agent stopped")


def cmd_status():
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = f.read().strip()
        if os.path.exists(f"/proc/{pid}"):
            print(f"Agent running (PID {pid})")
        else:
            print(f"Stale PID file ({pid}), agent not running")
    else:
        print("Agent not running")
    cfg = load_config()
    print(f"Gateway: {cfg.gateway_id}")
    print(f"Home:    {cfg.home_id or '(not paired)'}")
    print(f"Source:  {cfg.source}")
    print(f"API:     {cfg.api_url}")
    print(f"Token:   {'set' if cfg.api_token else 'not set'}")


def main():
    parser = argparse.ArgumentParser(description="Ligerwave Router CSI Agent")
    parser.add_argument("--pair", action="store_true", help="Start QR pairing")
    parser.add_argument("--daemon", action="store_true", help="Run CSI capture daemon")
    parser.add_argument("--status", action="store_true", help="Show agent status")
    args = parser.parse_args()

    if args.pair:
        cmd_pair()
    elif args.daemon:
        cmd_daemon()
    elif args.status:
        cmd_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
