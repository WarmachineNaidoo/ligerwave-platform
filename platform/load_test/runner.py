"""
Async load tester for WiFi CSI intrusion detection platform.

Simulates N virtual homes each pushing real-time CSI measurements at a
configurable rate, with a fraction of packets carrying intrusion signatures.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import math
import os
import signal
import sys
import time
from dataclasses import dataclass, field
from statistics import mean, stdev

import httpx
import numpy as np

CSI_ANTENNAS = 3
CSI_SUBCARRIERS = 52
CSI_SHAPE = (CSI_ANTENNAS, CSI_SUBCARRIERS)


@dataclass
class Stats:
    sent: int = 0
    accepted: int = 0
    latencies: list[float] = field(default_factory=list)
    errors: int = 0

    @property
    def avg_latency_ms(self) -> float:
        return mean(self.latencies) * 1000 if self.latencies else 0.0

    @property
    def p99_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * 0.99)
        return sorted_l[idx] * 1000

    @property
    def error_rate(self) -> float:
        return self.errors / self.sent if self.sent else 0.0


def make_csi_frame(intrusion: bool) -> str:
    data = np.random.randn(*CSI_SHAPE).astype(np.float32)
    if intrusion:
        mask = np.random.choice(
            [True, False], size=CSI_SHAPE, p=[0.3, 0.7]
        )
        data[mask] *= 1.3
    return data.tobytes().hex()


async def simulate_home(
    home_id: str,
    device_id: str,
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    interval_s: float,
    intrusion_ratio: float,
    duration_s: float,
    stats: Stats,
    stop: asyncio.Event,
    progress: asyncio.Event,
):
    deadline = time.monotonic() + duration_s
    while time.monotonic() < deadline and not stop.is_set():
        t0 = time.monotonic()
        intrusion = np.random.random() < intrusion_ratio
        payload = {
            "gateway_id": device_id,
            "firmware_ver": "2.1.0",
            "csi_data_hex": make_csi_frame(intrusion),
            "event_type": "intrusion" if intrusion else "normal",
            "confidence": round(0.3 + np.random.random() * 0.7, 4),
            "zone": np.random.choice(
                ["living_room", "bedroom", "kitchen", "hallway", "garage"]
            ),
            "wifi_signal_dbm": int(-55 + np.random.random() * 20),
            "uptime_s": int(np.random.random() * 86400),
        }
        try:
            resp = await client.post(
                f"{base_url}/devices/events?home_id={home_id}",
                json=payload,
                timeout=10,
            )
            stats.sent += 1
            stats.latencies.append(time.monotonic() - t0)
            if resp.status_code in (200, 201):
                stats.accepted += 1
            else:
                stats.errors += 1
        except Exception:
            stats.sent += 1
            stats.errors += 1

        elapsed = time.monotonic() - t0
        sleep = max(0.0, interval_s - elapsed)
        await asyncio.sleep(sleep)

    if progress.is_set():
        print(f"  {home_id} done")


async def reporter(stats_list: list[Stats], total_homes: int, done: asyncio.Event):
    try:
        import tqdm

        bar = tqdm.tqdm(
            total=None,
            unit="req",
            desc="CSI load test",
            bar_format="{desc}: {rate_fmt} | sent:{postfix[0]} ok:{postfix[1]} err:{postfix[2]}",
        )
        while not done.is_set():
            s = Stats()
            for st in stats_list:
                s.sent += st.sent
                s.accepted += st.accepted
                s.errors += st.errors
            bar.postfix = (s.sent, s.accepted, s.errors)
            bar.update(0)
            await asyncio.sleep(1)
        bar.close()
    except ImportError:
        pass


async def main():
    parser = argparse.ArgumentParser(
        description="WiFi CSI intrusion detection load tester"
    )
    parser.add_argument("--homes", type=int, default=10, help="Number of virtual homes")
    parser.add_argument(
        "--rate", type=int, default=100, help="Target total packets per second"
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Test duration in seconds"
    )
    parser.add_argument(
        "--intrusion-ratio",
        type=float,
        default=0.05,
        help="Fraction of packets with intrusion signature",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("BASE_URL", "http://localhost:8000"),
        help="Base URL of the API",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("JWT_TOKEN", ""),
        help="Bearer token for authentication",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path for CSV output (auto-generated if not provided)",
    )
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    args = parser.parse_args()

    homes = args.homes
    rate = args.rate
    duration = args.duration
    interval_s = homes / rate if rate > 0 else 0.01
    intrusion_ratio = max(0.0, min(1.0, args.intrusion_ratio))
    base_url = args.base_url.rstrip("/")

    if interval_s < 0.001:
        print("error: rate too high for the number of homes", file=sys.stderr)
        sys.exit(1)

    print(
        f"Starting load test: {homes} homes, {rate} req/s, {duration}s, "
        f"intrusion_ratio={intrusion_ratio:.0%}"
    )
    print(f"Target: {base_url}")
    print()

    stop = asyncio.Event()
    progress = asyncio.Event()
    progress.set()
    done = asyncio.Event()
    stats_list = [Stats() for _ in range(homes)]

    def on_sigint():
        print("\nShutdown requested — finishing in-flight requests...")
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, on_sigint)
        except NotImplementedError:
            pass

    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    async with httpx.AsyncClient(headers=headers, limits=httpx.Limits(max_keepalive_connections=homes * 2)) as client:
        tasks = []
        for i in range(homes):
            task = asyncio.create_task(
                simulate_home(
                    home_id=f"home-{i:04d}",
                    device_id=f"device-{i:04d}",
                    client=client,
                    base_url=base_url,
                    token=args.token,
                    interval_s=interval_s,
                    intrusion_ratio=intrusion_ratio,
                    duration_s=duration,
                    stats=stats_list[i],
                    stop=stop,
                    progress=progress,
                )
            )
            tasks.append(task)

        if not args.no_progress:
            tasks.append(
                asyncio.create_task(reporter(stats_list, homes, done))
            )

        await asyncio.gather(*tasks, return_exceptions=True)
        done.set()

    total = Stats()
    for st in stats_list:
        total.sent += st.sent
        total.accepted += st.accepted
        total.errors += st.errors
        total.latencies.extend(st.latencies)

    print()
    print("=== Summary ===")
    print(f"  Total sent:       {total.sent}")
    print(f"  Accepted (2xx):   {total.accepted}")
    print(f"  Errors:           {total.errors}")
    print(f"  Error rate:       {total.error_rate:.2%}")
    if total.latencies:
        print(f"  Avg latency:      {total.avg_latency_ms:.1f} ms")
        print(f"  P99 latency:      {total.p99_latency_ms:.1f} ms")
        print(f"  Min latency:      {min(total.latencies) * 1000:.1f} ms")
        print(f"  Max latency:      {max(total.latencies) * 1000:.1f} ms")

    csv_path = args.output or f"load_test_{int(time.time())}.csv"
    if total.latencies:
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["home_idx", "latency_s", "accepted", "error"])
            for i, st in enumerate(stats_list):
                for lat in st.latencies:
                    w.writerow([i, round(lat, 6), int(st.accepted > 0), int(st.errors > 0)])
        print(f"\n  CSV output:       {csv_path}")


if __name__ == "__main__":
    asyncio.run(main())
