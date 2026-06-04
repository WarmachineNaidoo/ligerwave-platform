# Ligerwave Drone — Phase 2 & 3 API Specification

## Phase 2: Camera Fusion (CSI Heatmap Overlay on Video)

### Endpoint: GET /drone/overlay/{session_id}
Returns CSI heatmap data formatted for camera overlay rendering.

```
Response:
{
  "session_id": "...",
  "grid_size": 20,
  "heat": [[0.0, 0.1, ...], ...],
  "persons": [
    {"x": 5.2, "y": 3.1, "confidence": 0.87, "bpm": 72},
    {"x": 12.8, "y": 8.4, "confidence": 0.65, "bpm": 95}
  ],
  "target": {"x": 5.2, "y": 3.1, "bpm": 72, "tone": "calm"},
  "camera_transform": {
    "altitude": 50.0,
    "heading": 180.0,
    "pitch": -90.0
  }
}
```

### Integration: DJI Mobile SDK / MAVSDK
The drone app:
1. Receives video frame from drone camera
2. Overlays CSI heatmap as semi-transparent grid
3. Renders person markers with HR data
4. Highlights target with tracking ring

### Implementation
- `routers/drone.py` — DroneAPI endpoints
- `services/drone.py` — Session management, camera alignment
- WebSocket `/ws/trace/{session_id}` — Real-time BPM + heatmap push (already exists)

---

## Phase 3: Autonomous Visual Follow + CSI Backup

### Architecture
```
Drone camera → Onboard tracking (DJI ActiveTrack / OpenCV)
  ├── Target visible → visual tracking (standard, low latency)
  └── Target lost (behind cover) → CSI takes over (50m range)
       └── CSI guides drone to target's last known position
```

### Endpoint: POST /drone/track
```
Request: {
  "session_id": "...",
  "target_gait": "...",
  "last_visual_position": {"lat": -29.85, "lng": 31.02}
}

Response: {
  "status": "tracking",
  "mode": "visual|csi|hybrid",
  "target_position": {"x": 5.2, "y": 3.1},
  "confidence": 0.87,
  "drone_command": "move_to(29.85, 31.02, 50.0)"
}
```

### Endpoint: POST /drone/reacquire
When visual tracking lost + CSI shows target behind nearby structure:
```
Request: {
  "session_id": "...",
  "last_known_position": {"x": 5, "y": 3},
  "drone_position": {"altitude": 50, "heading": 180}
}

Response: {
  "target_behind": {"wall_angle": 90, "distance": 8.5},
  "recommended_drone_position": {"altitude": 30, "heading": 270},
  "expected_reacquire_time_seconds": 5
}
```

### Drone Commands
- `move_to(lat, lng, alt)` — Navigate to GPS coordinate
- `rotate(heading)` — Point camera in direction
- `descend(altitude)` — Lower altitude for better CSI through-wall resolution
- `hover()` — Maintain position while CSI reacquires target

---

## Build Plan

| Component | Effort | Dependencies |
|-----------|--------|--------------|
| `routers/drone.py` + `services/drone.py` | 2 days | Trace app already built |
| DJI Mobile SDK integration (overlay) | 2 weeks | DJI developer account, test drone |
| Camera- CSI coordinate alignment | 1 week | Calibration with real drone footage |
| Autonomous follow logic | 2 weeks | Phase 2 complete + drone SDK |
| **Total Phase 2+3** | **~5 weeks** | Requires physical drone for testing |
