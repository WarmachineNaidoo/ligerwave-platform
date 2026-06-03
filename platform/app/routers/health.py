from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from app.database import service
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from app.config import settings as app_settings
from datetime import datetime, timezone, timedelta
import secrets, json, io, httpx

router = APIRouter(prefix="/health", tags=["health"])

def _headers():
    return {"apikey": app_settings.supabase_service_key, "Authorization": "Bearer " + app_settings.supabase_service_key}

# --- Sleep Apnea ---

@router.get("/{home_id}/apnea")
async def get_apnea(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    """Get latest apnea data for a home."""
    from app.services.wellness import apnea_detectors
    detector = apnea_detectors.get(home_id)
    if not detector:
        return {"status": "not_initialized", "ahi": 0, "apneas": 0, "hypopneas": 0, "severity": "unknown"}
    return detector.detect_apnea()

@router.get("/{home_id}/apnea/history")
async def apnea_history(home_id: str = Depends(verify_home_ownership), days: int = Query(7, ge=1, le=90), payload: dict = Depends(get_current_user)):
    """Get apnea event history."""
    events = service.table("events").select("*").eq("home_id", home_id).eq("event_type", "apnea").gte("timestamp", (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()).order("timestamp", desc=True).execute()
    return {"events": events.data or [], "total": len(events.data or [])}

# --- EDF Export ---

@router.get("/{home_id}/sleep/export/edf")
async def export_edf(
    home_id: str = Depends(verify_home_ownership),
    nights: int = Query(7, ge=1, le=90),
    payload: dict = Depends(get_current_user),
):
    """Export sleep breathing data as EDF (European Data Format) for import into sleep scoring software."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=nights)).isoformat()
    events = service.table("events").select("confidence,timestamp").eq("home_id", home_id).eq("event_type", "breathing").gte("timestamp", cutoff).order("timestamp", asc=True).execute()
    rows = events.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="No breathing data found for this period")

    timestamps = []
    values = []
    for r in rows:
        c = r.get("confidence")
        if c:
            ts = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
            timestamps.append(ts)
            values.append(c * 60)  # Convert to BPM

    if len(values) < 10:
        raise HTTPException(status_code=400, detail="Not enough data points for EDF export (minimum 10)")

    start = timestamps[0]
    duration_s = (timestamps[-1] - start).total_seconds()
    n_records = max(1, int(duration_s))

    # Build EDF binary
    edf = bytearray()

    def pad(s, length):
        return s.encode("ascii").ljust(length)[:length]

    # --- Header (256 bytes) ---
    edf += pad("0", 8)                                                    # version
    edf += pad(f"Ligerwave CSI Home {home_id[:8]}", 80)                 # patient ID
    edf += pad(f"Startup X Sleep Breathing X X Ligerwave", 80)           # recording info
    edf += pad(start.strftime("%d.%m.%y"), 8)                            # start date
    edf += pad(start.strftime("%H.%M.%S"), 8)                            # start time
    edf += pad(str(256 + 1 * 256), 8)                                     # header size
    edf += pad("", 44)                                                    # reserved
    edf += pad(str(n_records), 8)                                         # num records
    edf += pad("1", 8)                                                    # duration per record (sec)
    edf += pad("1", 4)                                                    # num signals

    # --- Signal header (256 bytes per signal) ---
    edf += pad("BreathingRate", 16)                                       # label
    edf += pad("CSI envelope", 80)                                        # transducer
    edf += pad("BPM", 8)                                                  # physical dimension
    edf += pad(str(min(values)), 8)                                       # physical min
    edf += pad(str(max(values)), 8)                                       # physical max
    edf += pad("-32768", 8)                                               # digital min
    edf += pad("32767", 8)                                                # digital max
    edf += pad("", 80)                                                    # prefilters
    edf += pad("1", 8)                                                    # samples per record per signal
    edf += pad("", 32)                                                    # reserved

    # --- Data ---
    # Resample values to 1 Hz over the duration
    import numpy as np
    data_times = np.array([(t - start).total_seconds() for t in timestamps])
    uniform_times = np.linspace(0, duration_s, n_records)
    resampled = np.interp(uniform_times, data_times, np.array(values, dtype=float))
    resampled_int = np.clip(np.round(resampled).astype(np.int16), -32768, 32767)

    for v in resampled_int:
        edf += v.tobytes()

    return StreamingResponse(io.BytesIO(bytes(edf)), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="ligerwave_sleep_{home_id[:8]}_{start.strftime("%Y%m%d")}.edf"'})

# --- Health Data Sharing ---

class ShareLink(BaseModel):
    expires_days: int = Field(default=7, ge=1, le=365)
    data_types: List[str] = Field(default=["sleep_quality", "apnea", "breathing"])
    name: Optional[str] = None

@router.post("/{home_id}/share")
async def create_share_link(body: ShareLink, home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    """Generate a shareable link to health data."""
    user_id = payload.get("sub")
    code = secrets.token_urlsafe(24)
    meta_r = httpx.get(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=_headers())
    meta = meta_r.json().get("user_metadata", {}) or {} if meta_r.status_code == 200 else {}
    shares = meta.get("health_shares", [])
    share = {
        "id": code[:12],
        "code": code,
        "home_id": home_id,
        "created_by": user_id,
        "name": body.name or "Unnamed Report",
        "data_types": body.data_types,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=body.expires_days)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "views": 0,
    }
    shares.append(share)
    meta["health_shares"] = shares
    httpx.put(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers={**_headers(), "Content-Type": "application/json"}, json={"user_metadata": meta})
    return {"share_code": code, "share_url": f"/health/share/{code}", "expires_at": share["expires_at"]}

@router.get("/share/{code}")
async def view_share(code: str):
    """View shared health data (public, no auth needed)."""
    # Scan users for this share code
    users_r = httpx.get(f"{app_settings.supabase_url}/auth/v1/admin/users", headers=_headers())
    if users_r.status_code != 200:
        raise HTTPException(status_code=500, detail="Cannot lookup share")
    for u in users_r.json().get("users", []):
        meta = u.get("user_metadata") or {}
        for share in (meta.get("health_shares") or []):
            if share.get("code") == code:
                if share.get("expires_at", "") < datetime.now(timezone.utc).isoformat():
                    raise HTTPException(status_code=410, detail="Share link expired")
                share["views"] = share.get("views", 0) + 1
                meta["health_shares"] = [s if s.get("id") != share["id"] else share for s in (meta.get("health_shares") or [])]
                httpx.put(f"{app_settings.supabase_url}/auth/v1/admin/users/{u['id']}", headers={**_headers(), "Content-Type": "application/json"}, json={"user_metadata": meta})
                # Build health report
                home_id = share["home_id"]
                data_types = share.get("data_types", ["sleep_quality", "apnea", "breathing"])
                report = {"home_id": home_id, "shared_by": u.get("email", ""), "data_types": data_types}
                if "sleep_quality" in data_types:
                    sleep = service.table("events").select("*").eq("home_id", home_id).eq("event_type", "breathing").gte("timestamp", (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()).order("timestamp", desc=True).limit(500).execute()
                    report["sleep_quality"] = sleep.data or []
                if "apnea" in data_types:
                    apnea = service.table("events").select("*").eq("home_id", home_id).eq("event_type", "apnea").order("timestamp", desc=True).limit(200).execute()
                    report["apnea_events"] = apnea.data or []
                if "breathing" in data_types:
                    breath = service.table("events").select("*").eq("home_id", home_id).eq("event_type", "breathing").order("timestamp", desc=True).limit(200).execute()
                    report["breathing_history"] = breath.data or []
                return HTMLResponse(_render_health_report(report))
    raise HTTPException(status_code=404, detail="Share link not found")

@router.get("/{home_id}/shares")
async def list_shares(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta_r = httpx.get(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=_headers())
    meta = meta_r.json().get("user_metadata", {}) or {} if meta_r.status_code == 200 else {}
    shares = [s for s in (meta.get("health_shares") or []) if s.get("home_id") == home_id]
    return [{"id": s["id"], "name": s.get("name"), "data_types": s.get("data_types"), "expires_at": s.get("expires_at"), "views": s.get("views", 0), "created_at": s.get("created_at")} for s in shares]

@router.delete("/{home_id}/shares/{share_id}")
async def delete_share(home_id: str = Depends(verify_home_ownership), share_id: str = None, payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    meta_r = httpx.get(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers=_headers())
    meta = meta_r.json().get("user_metadata", {}) or {} if meta_r.status_code == 200 else {}
    meta["health_shares"] = [s for s in (meta.get("health_shares") or []) if s.get("id") != share_id]
    httpx.put(f"{app_settings.supabase_url}/auth/v1/admin/users/{user_id}", headers={**_headers(), "Content-Type": "application/json"}, json={"user_metadata": meta})
    return {"status": "deleted"}

# --- Health Report PDF ---

@router.get("/{home_id}/report")
async def health_report_pdf(home_id: str = Depends(verify_home_ownership), days: int = Query(30, ge=1, le=365), payload: dict = Depends(get_current_user)):
    """Generate a PDF health report."""
    from app.services.health_report import generate_health_report
    buf = generate_health_report(home_id, days)
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=health_report_{home_id[:8]}.pdf"})

# --- Escalation Config ---

@router.get("/{home_id}/escalation")
async def get_escalation_config(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    from app.services.escalation import escalation_protocols, EscalationProtocol
    if home_id not in escalation_protocols:
        escalation_protocols[home_id] = EscalationProtocol(home_id)
    return escalation_protocols[home_id].get_config()

@router.put("/{home_id}/escalation")
async def update_escalation_config(body: dict, home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    from app.services.escalation import escalation_protocols, EscalationProtocol
    if home_id not in escalation_protocols:
        escalation_protocols[home_id] = EscalationProtocol(home_id)
    escalation_protocols[home_id].save_config(body)
    return {"status": "updated"}

# --- Escalation Contacts ---

@router.post("/{home_id}/escalation/contacts")
async def update_contacts(body: dict, home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    from app.services.escalation import escalation_protocols, EscalationProtocol
    if home_id not in escalation_protocols:
        escalation_protocols[home_id] = EscalationProtocol(home_id)
    cfg = escalation_protocols[home_id].get_config()
    cfg["contacts"] = body
    escalation_protocols[home_id].save_config(cfg)
    return {"status": "updated"}

@router.post("/{home_id}/escalation/acknowledge")
async def acknowledge_alert(event_id: str = Query(...), by: str = Query("user"), home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    from app.services.escalation import escalation_protocols
    if home_id in escalation_protocols:
        escalation_protocols[home_id].acknowledge(event_id, by)
    return {"status": "acknowledged"}


# --- Dark Mode Baseline ---

@router.get("/{home_id}/baseline")
async def baseline_status(home_id: str = Depends(verify_home_ownership), payload: dict = Depends(get_current_user)):
    from app.services.baseline import baselines, HomeBaseline
    if home_id not in baselines:
        baselines[home_id] = HomeBaseline(home_id)
    return baselines[home_id].get_status()


# --- Ops Monitoring ---

@router.get("/ops/health")
async def ops_health(payload: dict = Depends(get_current_user)):
    user = service.table("users").select("role").eq("id", payload.get("sub")).execute()
    if not user.data or user.data[0].get("role") not in ("admin", "staff"):
        raise HTTPException(status_code=403, detail="Admin access required")
    supabase_ok = False
    try:
        service.table("homes").select("count", count="exact").limit(1).execute()
        supabase_ok = True
    except Exception:
        pass
    r2_ok = False
    try:
        import httpx
        if app_settings.r2_endpoint:
            r = httpx.get(app_settings.r2_endpoint, timeout=5)
            r2_ok = r.status_code < 500
    except Exception:
        pass
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    recent = service.table("events").select("count", count="exact").gte("timestamp", cutoff).execute()
    total_5min = recent.count if hasattr(recent, 'count') else len(recent.data or [])
    homes_resp = service.table("homes").select("count", count="exact").execute()
    active_homes = homes_resp.count if hasattr(homes_resp, 'count') else len(homes_resp.data or [])
    return {
        "status": "healthy" if supabase_ok else "degraded",
        "supabase": supabase_ok,
        "r2": r2_ok,
        "active_homes": active_homes,
        "events_last_5min": total_5min,
        "ingestion_rate_per_min": round(total_5min / 5, 1),
    }

@router.get("/ops/homes")
async def ops_homes(payload: dict = Depends(get_current_user)):
    user = service.table("users").select("role").eq("id", payload.get("sub")).execute()
    if not user.data or user.data[0].get("role") not in ("admin", "staff"):
        raise HTTPException(status_code=403, detail="Admin access required")
    homes = service.table("homes").select("id,name,address,status,tier,created_at").execute()
    results = []
    for h in (homes.data or []):
        e = service.table("events").select("timestamp").eq("home_id", h["id"]).order("timestamp", desc=True).limit(1).execute()
        last_event = e.data[0]["timestamp"] if e.data else None
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        count_r = service.table("events").select("count", count="exact").eq("home_id", h["id"]).gte("timestamp", cutoff).execute()
        event_count = count_r.count if hasattr(count_r, 'count') else len(count_r.data or [])
        dev = service.table("devices").select("last_seen").eq("home_id", h["id"]).execute()
        device_online = False
        if dev.data and dev.data[0].get("last_seen"):
            last = datetime.fromisoformat(dev.data[0]["last_seen"].replace("Z", "+00:00"))
            device_online = (datetime.now(timezone.utc) - last).total_seconds() < 300
        results.append({
            "id": h["id"],
            "name": h.get("name"),
            "status": h.get("status"),
            "tier": h.get("tier"),
            "last_event": last_event,
            "events_24h": event_count,
            "device_online": device_online,
        })
    return {"homes": results, "total": len(results)}

@router.get("/ops/homes/{home_id}/latency")
async def ops_home_latency(home_id: str, payload: dict = Depends(get_current_user)):
    user = service.table("users").select("role").eq("id", payload.get("sub")).execute()
    if not user.data or user.data[0].get("role") not in ("admin", "staff"):
        raise HTTPException(status_code=403, detail="Admin access required")
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    events = service.table("events").select("timestamp,id,event_type").eq("home_id", home_id).gte("timestamp", cutoff).order("timestamp", desc=True).limit(100).execute()
    items = []
    now = datetime.now(timezone.utc)
    for e in (events.data or []):
        ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
        age_s = (now - ts).total_seconds()
        items.append({"id": e["id"], "event_type": e.get("event_type"), "timestamp": e["timestamp"], "age_seconds": round(age_s, 1)})
    return {
        "home_id": home_id,
        "events": items,
        "oldest_event_seconds": max(i["age_seconds"] for i in items) if items else 0,
        "newest_event_seconds": min(i["age_seconds"] for i in items) if items else 0,
    }


def _render_health_report(report: Dict) -> str:
    """Render a static HTML health report page."""
    home_id = report.get("home_id", "unknown")
    shared_by = report.get("shared_by", "Unknown")
    sleep_data = report.get("sleep_quality", [])
    apnea_data = report.get("apnea_events", [])
    breath_data = report.get("breathing_history", [])

    # Calculate averages
    bpm_values = [e.get("confidence", 0) * 15 + 12 for e in breath_data if e.get("confidence")]
    avg_bpm = round(sum(bpm_values) / len(bpm_values), 1) if bpm_values else "--"
    apnea_count = len(apnea_data)
    sleep_hours = round(len(sleep_data) * 0.1, 1) if sleep_data else 0
    sleep_score = round((1 - apnea_count / max(len(breath_data), 1)) * 100, 0) if breath_data else 0

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Health Report — Ligerwave</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,-apple-system,sans-serif}}
body{{background:#0f172a;color:#e2e8f0;padding:20px;max-width:800px;margin:0 auto}}
h1{{font-size:24px;font-weight:600;margin-bottom:4px;color:#22d3ee}}
.sub{{color:#94a3b8;font-size:13px;margin-bottom:20px}}
.card{{background:#1e293b;border-radius:10px;padding:16px;margin-bottom:12px;border-left:3px solid #334155}}
.card h2{{font-size:14px;color:#94a3b8;font-weight:500;margin-bottom:8px}}
.stat-row{{display:flex;gap:16px;flex-wrap:wrap}}
.stat{{flex:1;min-width:100px}}
.stat .val{{font-size:28px;font-weight:700;color:#22d3ee}}
.stat .lbl{{font-size:11px;color:#64748b;text-transform:uppercase}}
.severity{{padding:4px 12px;border-radius:6px;font-size:12px;font-weight:600;display:inline-block}}
.severity.normal{{background:#064e3b;color:#6ee7b7}}
.severity.mild{{background:#7c2d12;color:#fdba74}}
.severity.moderate{{background:#7f1d1d;color:#fca5a5}}
.severity.severe{{background:#7f1d1d;color:#fca5a5;border:1px solid #ef4444}}
.footer{{text-align:center;color:#475569;font-size:11px;margin-top:30px;padding-top:16px;border-top:1px solid #1e293b}}
</style>
</head><body>
<h1>🩺 Ligerwave Health Report</h1>
<div class="sub">Shared by {shared_by} | Home: {home_id[:8]}... | Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC</div>

<div class="card">
  <h2>Sleep Summary</h2>
  <div class="stat-row">
    <div class="stat"><div class="val">{avg_bpm}</div><div class="lbl">Avg BPM</div></div>
    <div class="stat"><div class="val">{sleep_hours}h</div><div class="lbl">Sleep Tracked</div></div>
    <div class="stat"><div class="val">{sleep_score}%</div><div class="lbl">Sleep Score</div></div>
  </div>
</div>

<div class="card">
  <h2>Apnea Analysis</h2>
  <div style="margin-bottom:8px">
    <span class="severity {'severe' if apnea_count > 30 else 'moderate' if apnea_count > 15 else 'mild' if apnea_count > 5 else 'normal'}">{'SEVERE' if apnea_count > 30 else 'MODERATE' if apnea_count > 15 else 'MILD' if apnea_count > 5 else 'NORMAL'}</span>
  </div>
  <div class="stat-row">
    <div class="stat"><div class="val">{apnea_count}</div><div class="lbl">Total Events</div></div>
    <div class="stat"><div class="val">{round(apnea_count / max(sleep_hours, 1), 1)}</div><div class="lbl">Events/Hour</div></div>
  </div>
</div>

<div class="card">
  <h2>Breathing History ({len(breath_data)} samples)</h2>
  <div style="height:100px;display:flex;align-items:flex-end;gap:1px">
    {''.join(f'<div style="flex:1;background:#22d3ee;height:{min(100, e.get("confidence", 0) * 100)}px;border-radius:1px;opacity:0.6"></div>' for e in breath_data[-100:])}
  </div>
</div>

<div class="card">
  <h2>Disclaimer</h2>
  <p style="font-size:12px;color:#64748b">This data is for informational purposes only and is not a medical diagnosis. Consult a healthcare professional for medical advice.</p>
</div>

<div class="footer">Ligerwave WiFi CSI Security Platform | Privacy-First</div>
</body></html>"""
