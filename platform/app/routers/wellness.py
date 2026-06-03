from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from app.database import service
from app.middleware.auth import get_current_user, require_role
from app.middleware.ownership import verify_home_ownership
from app.services.wellness import breathing_detectors, fall_detectors, apnea_detectors, BreathingDetector, FallDetector, ApneaDetector
from app.services.signal import processors, CsiProcessor
from datetime import datetime, timezone, timedelta
import numpy as np, binascii
from app.services.log import logger

router = APIRouter(prefix="/wellness", tags=["wellness"])

@router.get("/{home_id}/breathing")
async def get_breathing(
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user),
):
    if home_id not in breathing_detectors:
        breathing_detectors[home_id] = BreathingDetector(home_id)
    detector = breathing_detectors[home_id]
    result = detector.detect()

    history = service.table("events").select("confidence,timestamp").eq("home_id", home_id).eq("event_type", "breathing").order("timestamp", desc=True).limit(60).execute()
    recent = []
    for e in history.data or []:
        rate = e.get("confidence")
        if rate:
            recent.append({"time": e["timestamp"][:19], "rate_bpm": round(rate * 60, 1)})

    return {"home_id": home_id, **result, "history": recent}

@router.get("/{home_id}/breathing/history")
async def get_breathing_history(
    home_id: str = Depends(verify_home_ownership),
    days: int = Query(7, ge=1, le=30),
    payload: dict = Depends(get_current_user),
):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    events = service.table("events").select("confidence,timestamp").eq("home_id", home_id).eq("event_type", "breathing").gte("timestamp", cutoff).order("timestamp", desc=True).execute()
    history = []
    for e in events.data or []:
        rate = e.get("confidence")
        if rate:
            history.append({"time": e["timestamp"][:19], "rate_bpm": round(rate * 60, 1)})

    avg_rate = np.mean([h["rate_bpm"] for h in history]) if history else 0
    return {
        "home_id": home_id,
        "days": days,
        "samples": len(history),
        "average_rate_bpm": round(float(avg_rate), 1),
        "history": history[-200:],
    }

@router.get("/{home_id}/fall")
async def get_fall_status(
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user),
):
    if home_id not in fall_detectors:
        fall_detectors[home_id] = FallDetector(home_id)
    detector = fall_detectors[home_id]
    result = detector.detect()

    recent = service.table("events").select("*").eq("home_id", home_id).eq("event_type", "fall").order("timestamp", desc=True).limit(10).execute()
    return {"home_id": home_id, **result, "recent_falls": recent.data or []}

@router.get("/{home_id}/apnea")
async def get_apnea_status(
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user),
):
    if home_id not in apnea_detectors:
        apnea_detectors[home_id] = ApneaDetector(home_id)
    return apnea_detectors[home_id].detect_apnea()

@router.get("/{home_id}/apnea/history")
async def get_apnea_history(
    home_id: str = Depends(verify_home_ownership),
    days: int = Query(7, ge=1, le=90),
    payload: dict = Depends(get_current_user),
):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    events = service.table("events").select("*").eq("home_id", home_id).eq("event_type", "apnea").gte("timestamp", cutoff).order("timestamp", desc=True).execute()
    return {"events": events.data or [], "total": len(events.data or [])}

@router.post("/{home_id}/process")
async def process_wellness(
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user),
):
    csi_events = service.table("events").select("id,csi_size_bytes,timestamp").eq("home_id", home_id).gt("csi_size_bytes", 0).order("timestamp", desc=True).limit(50).execute()
    if not csi_events.data:
        raise HTTPException(status_code=404, detail="No CSI events found")

    if home_id not in breathing_detectors:
        breathing_detectors[home_id] = BreathingDetector(home_id)
    if home_id not in fall_detectors:
        fall_detectors[home_id] = FallDetector(home_id)
    if home_id not in apnea_detectors:
        apnea_detectors[home_id] = ApneaDetector(home_id)

    bd = breathing_detectors[home_id]
    fd = fall_detectors[home_id]
    ad = apnea_detectors[home_id]

    count = 0
    for event in reversed(csi_events.data):
        csi = service.table("csi_raw").select("storage_path").eq("event_id", event["id"]).execute()
        if not csi.data:
            continue
        try:
            from app.services.storage import get_csi
            csi_bytes = get_csi(event["id"])
            data = np.frombuffer(csi_bytes, dtype=np.float32)
            if data.size >= 156:
                amplitude = data[:156].reshape(3, 52)
                bd.add_packet(amplitude)
                fd.add_packet(amplitude)
                # Feed apnea detector with mean amplitude
                ad.add_envelope_sample(float(np.mean(np.abs(amplitude))))
                count += 1
        except Exception as e:
            logger.warning("process_wellness_failed", extra={"extra": {"action": "process_csi", "error": str(e)}})

    breath = bd.detect()
    fall = fd.detect()

    if breath.get("breathing_rate_bpm") and breath["confidence"] > 0.5:
        service.table("events").insert({
            "home_id": home_id,
            "event_type": "breathing",
            "confidence": breath["breathing_rate_bpm"] / 60.0,
            "zone": "wellness",
        }).execute()

    if fall.get("fall_confidence", 0) > 0.6:
        service.table("events").insert({
            "home_id": home_id,
            "event_type": "fall",
            "confidence": fall["fall_confidence"],
            "zone": "wellness",
        }).execute()

    apnea = ad.detect_apnea()
    if apnea.get("status") == "active" and apnea.get("ahi", 0) > 0:
        service.table("events").insert({
            "home_id": home_id,
            "event_type": "apnea",
            "confidence": min(1.0, apnea["ahi"] / 50.0),
            "zone": "wellness",
            "metadata": {"ahi": apnea["ahi"], "severity": apnea.get("severity", "normal"), "total_events": apnea.get("total_events", 0), "apneas": apnea.get("apneas", 0), "hypopneas": apnea.get("hypopneas", 0)}
        }).execute()

    return {
        "processed": count,
        "breathing": breath,
        "fall": fall,
        "apnea": apnea,
    }

@router.get("/{home_id}/sleep")
async def get_sleep_quality(
    home_id: str = Depends(verify_home_ownership),
    nights: int = Query(7, ge=1, le=30),
    payload: dict = Depends(get_current_user),
):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=nights)).isoformat()
    events = service.table("events").select("confidence,timestamp").eq("home_id", home_id).eq("event_type", "breathing").gte("timestamp", cutoff).order("timestamp", desc=True).execute()

    nights_data = {}
    for e in events.data or []:
        rate = e.get("confidence")
        if not rate:
            continue
        ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
        hour = ts.hour
        night_key = ts.strftime("%Y-%m-%d")
        if hour < 8:
            pass
        elif hour >= 20:
            night_key = (ts + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            continue

        bpm = round(rate * 60, 1)
        if night_key not in nights_data:
            nights_data[night_key] = {"rates": [], "first": ts.isoformat()}
        nights_data[night_key]["rates"].append(bpm)

    nights_list = []
    for night_key in sorted(nights_data.keys(), reverse=True)[:nights]:
        d = nights_data[night_key]
        rates = d["rates"]
        if len(rates) < 2:
            continue
        nights_list.append({
            "date": night_key,
            "samples": len(rates),
            "avg_bpm": round(float(np.mean(rates)), 1),
            "min_bpm": round(float(np.min(rates)), 1),
            "max_bpm": round(float(np.max(rates)), 1),
            "variability": round(float(np.std(rates)), 1),
            "first_reading": d["first"][:19],
        })

    overall = {"avg_bpm": 0, "variability": 0, "nights": 0}
    if nights_list:
        overall["avg_bpm"] = round(float(np.mean([n["avg_bpm"] for n in nights_list])), 1)
        overall["variability"] = round(float(np.mean([n["variability"] for n in nights_list])), 1)
        overall["nights"] = len(nights_list)

    return {"home_id": home_id, "nights": nights_list, "overall": overall}

@router.get("/{home_id}/sleep-efficiency")
async def get_sleep_efficiency(
    home_id: str = Depends(verify_home_ownership),
    nights: int = Query(1, ge=1, le=30),
    payload: dict = Depends(get_current_user),
):
    """Estimate sleep efficiency from motion events and breathing data."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=nights)).isoformat()
    motion_resp = service.table("events").select("event_type,timestamp").eq("home_id", home_id).eq("event_type", "motion").gte("timestamp", cutoff).order("timestamp", asc=True).execute()
    breath_resp = service.table("events").select("event_type,timestamp").eq("home_id", home_id).eq("event_type", "breathing").gte("timestamp", cutoff).order("timestamp", asc=True).execute()
    all_e = (motion_resp.data or []) + (breath_resp.data or [])

    # Group by night (8pm-8am)
    nights_map = {}
    for e in all_e:
        ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
        hour = ts.hour
        night_key = ts.strftime("%Y-%m-%d")
        if hour >= 20:
            night_key = (ts + timedelta(days=1)).strftime("%Y-%m-%d")
        elif hour < 8:
            pass
        else:
            continue  # outside sleep window

        if night_key not in nights_map:
            nights_map[night_key] = {"breathing": [], "motions": []}
        if e["event_type"] == "motion":
            nights_map[night_key]["motions"].append(ts.timestamp())
        elif e["event_type"] == "breathing":
            nights_map[night_key]["breathing"].append(ts.timestamp())

    nights_list = []
    for nk, ndata in sorted(nights_map.items(), reverse=True):
        b = ndata["breathing"]
        m = ndata["motions"]
        if len(b) < 10:
            continue
        bed_start = min(b)
        bed_end = max(b)
        total_min = (bed_end - bed_start) / 60.0
        # Count wake bouts: motion clusters separated by > 120s
        m_sorted = sorted(m)
        wake_clusters = []
        current_cluster = [m_sorted[0]] if m_sorted else []
        for i in range(1, len(m_sorted)):
            if m_sorted[i] - m_sorted[i-1] < 120:
                current_cluster.append(m_sorted[i])
            else:
                wake_clusters.append(current_cluster)
                current_cluster = [m_sorted[i]]
        if current_cluster:
            wake_clusters.append(current_cluster)

        wake_min = sum(max(0, (c[-1] - c[0])) for c in wake_clusters) / 60.0 if wake_clusters else 0
        sleep_min = max(1, total_min - wake_min)
        efficiency = min(100.0, (sleep_min / total_min) * 100.0) if total_min > 0 else 0
        nights_list.append({
            "date": nk,
            "bed_minutes": round(total_min, 0),
            "sleep_minutes": round(sleep_min, 0),
            "wake_minutes": round(wake_min, 0),
            "efficiency_pct": round(efficiency, 1),
            "motion_bouts": len(wake_clusters),
            "fragmentation_index": round((len(wake_clusters) / (total_min / 60)) if total_min > 60 else 0, 2),
        })

    avg_eff = round(float(np.mean([n["efficiency_pct"] for n in nights_list])), 1) if nights_list else 0
    return {"nights": nights_list, "average_efficiency": avg_eff, "nights_analyzed": len(nights_list)}

@router.get("/{home_id}/weekly-summary")
async def get_weekly_summary(
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user),
):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    events = service.table("events").select("event_type,confidence,timestamp").eq("home_id", home_id).gte("timestamp", cutoff).execute()
    all_events = events.data or []

    counts = {}
    for e in all_events:
        t = e.get("event_type", "unknown")
        counts[t] = counts.get(t, 0) + 1

    intrusion_alerts = [e for e in all_events if e.get("event_type") == "intrusion" and (e.get("confidence") or 0) >= 0.8]
    high_conf_intrusions = len(intrusion_alerts)

    armed_events = [e for e in all_events if e.get("event_type") in ("armed", "disarmed")]
    arms = sum(1 for e in armed_events if e.get("event_type") == "armed")
    disarms = sum(1 for e in armed_events if e.get("event_type") == "disarmed")

    breathing_events = [e for e in all_events if e.get("event_type") == "breathing"]
    fall_events = [e for e in all_events if e.get("event_type") == "fall"]

    avg_breathing = None
    if breathing_events:
        rates = [e.get("confidence", 0) * 60 for e in breathing_events if e.get("confidence")]
        if rates:
            avg_breathing = round(float(np.mean(rates)), 1)

    return {
        "home_id": home_id,
        "period_days": 7,
        "total_events": len(all_events),
        "by_type": counts,
        "high_confidence_intrusions": high_conf_intrusions,
        "arming_events": {"arms": arms, "disarms": disarms, "total": arms + disarms},
        "wellness": {
            "breathing_samples": len(breathing_events),
            "average_breathing_bpm": avg_breathing,
            "fall_events": len(fall_events),
        },
    }


@router.get("/{home_id}/report/weekly")
async def weekly_wellness_report(
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user),
):
    from app.services.health_report import generate_weekly_wellness_report
    buf = generate_weekly_wellness_report(home_id)
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=weekly_wellness_{home_id[:8]}.pdf"})
