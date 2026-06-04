import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict

GRID_SIZE = 20
DECAY_PER_SECOND = 0.05
TRAIL_DURATION = 60

ZONE_LAYOUT: Dict[str, Tuple[int, int, int, int]] = {
    "living_room": (2, 8, 10, 16),
    "kitchen": (12, 18, 2, 10),
    "dining": (10, 18, 12, 18),
    "bedroom": (2, 8, 2, 8),
    "bedroom_1": (2, 8, 2, 8),
    "bedroom_2": (2, 8, 10, 16),
    "bedroom_3": (10, 18, 2, 8),
    "bathroom": (10, 14, 10, 14),
    "hallway": (6, 14, 6, 10),
    "entrance": (14, 18, 14, 18),
    "garage": (0, 6, 12, 18),
    "office": (12, 18, 16, 20),
    "study": (12, 18, 16, 20),
    "default": (4, 16, 4, 16),
}

class TomographyFrame:
    def __init__(self):
        self.heat = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.trail = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.zones: Dict[str, List[Tuple[int, int]]] = {}
        self.last_update = datetime.now(timezone.utc)

class TomographyEngine:
    def __init__(self):
        self.frames: Dict[str, TomographyFrame] = {}

    def _get_frame(self, home_id: str) -> TomographyFrame:
        if home_id not in self.frames:
            self.frames[home_id] = TomographyFrame()
        return self.frames[home_id]

    def _zone_to_cells(self, zone_name: str) -> List[Tuple[int, int]]:
        zone_key = zone_name.lower().replace(" ", "_")
        box = ZONE_LAYOUT.get(zone_key, ZONE_LAYOUT["default"])
        y1, y2, x1, x2 = box
        cells = []
        for y in range(y1, min(y2, GRID_SIZE)):
            for x in range(x1, min(x2, GRID_SIZE)):
                cells.append((y, x))
        return cells

    def _label_zone_cells(self, home_id: str, zones: List[str]):
        frame = self._get_frame(home_id)
        for z in zones:
            if z not in frame.zones:
                frame.zones[z] = self._zone_to_cells(z)

    def ingest_event(self, home_id: str, zone: str, zone_path: List[str], confidence: float, timestamp: datetime):
        frame = self._get_frame(home_id)
        now = timestamp or datetime.now(timezone.utc)
        elapsed = (now - frame.last_update).total_seconds()
        if elapsed > 0:
            decay = np.exp(-DECAY_PER_SECOND * elapsed)
            frame.heat *= decay
            frame.trail *= decay
        frame.last_update = now
        all_zones = list(set([z for z in (zone_path or []) if z] + ([zone] if zone else [])))
        self._label_zone_cells(home_id, all_zones)
        if zone:
            for y, x in self._zone_to_cells(zone):
                frame.heat[y, x] = min(1.0, frame.heat[y, x] + confidence * 0.3)
        if zone_path:
            for i, z in enumerate(zone_path):
                weight = max(0.1, 1.0 - i * 0.15)
                for y, x in self._zone_to_cells(z):
                    frame.trail[y, x] = min(1.0, frame.trail[y, x] + confidence * weight * 0.2)

    def get_snapshot(self, home_id: str) -> dict:
        frame = self._get_frame(home_id)
        now = datetime.now(timezone.utc)
        elapsed = (now - frame.last_update).total_seconds()
        decay = np.exp(-DECAY_PER_SECOND * elapsed)
        heat = (frame.heat * decay).tolist()
        trail = (frame.trail * decay).tolist()
        zone_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int32)
        zone_colors: Dict[str, str] = {}
        color_palette = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"]
        znames = sorted(frame.zones.keys())
        zone_indices: Dict[str, int] = {}
        for i, zname in enumerate(znames):
            idx = i + 1
            zone_colors[zname] = color_palette[i % len(color_palette)]
            zone_indices[zname] = idx
            for y, x in frame.zones[zname]:
                zone_grid[y, x] = idx
        persons = self._detect_persons(frame)
        return {
            "grid_size": GRID_SIZE,
            "heat": heat,
            "trail": trail,
            "zone_grid": zone_grid.tolist(),
            "zone_colors": zone_colors,
            "zone_indices": zone_indices,
            "persons": persons,
            "updated_at": frame.last_update.isoformat(),
        }

    def _detect_persons(self, frame: TomographyFrame) -> List[dict]:
        persons = []
        heat = frame.heat
        threshold = 0.15
        used = set()
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if heat[y, x] > threshold and (y, x) not in used:
                    cluster = [(y, x)]
                    queue = [(y, x)]
                    used.add((y, x))
                    while queue:
                        cy, cx = queue.pop()
                        for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                            ny, nx = cy+dy, cx+dx
                            if 0 <= ny < GRID_SIZE and 0 <= nx < GRID_SIZE and (ny, nx) not in used and heat[ny, nx] > threshold:
                                used.add((ny, nx))
                                queue.append((ny, nx))
                                cluster.append((ny, nx))
                    if len(cluster) >= 3:
                        cy = sum(c[0] for c in cluster) / len(cluster)
                        cx = sum(c[1] for c in cluster) / len(cluster)
                        peak = max(heat[c[0], c[1]] for c in cluster)
                        persons.append({"x": round(cx, 1), "y": round(cy, 1), "confidence": round(float(peak), 3), "cells": len(cluster)})
        return persons

engines: Dict[str, TomographyEngine] = {}
