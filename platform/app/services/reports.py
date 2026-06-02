from datetime import datetime, timezone, timedelta
from app.database import supabase
from io import BytesIO
from typing import Optional

def generate_report(home_id: str, months: int = 1) -> BytesIO:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30 * months)).isoformat()
    events = supabase.table("events").select("*").eq("home_id", home_id).gte("timestamp", cutoff).execute()
    data = events.data or []
    total = len(data)
    intrusions = sum(1 for e in data if e.get("event_type") == "intrusion")
    motions = sum(1 for e in data if e.get("event_type") == "motion")
    avg_conf = sum(e.get("confidence", 0) or 0 for e in data) / max(total, 1)
    lines = [
        f"CSI Security Report — {home_id[:8]}...",
        f"Period: last {months} month(s)",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Total events: {total}",
        f"Intrusions: {intrusions}",
        f"Motion events: {motions}",
        f"Average confidence: {avg_conf:.1%}",
        "",
        "=== Event Log ===",
    ]
    for e in reversed(data[-100:]):
        lines.append(f"  {e.get('timestamp','')[:19]}  {e.get('event_type',''):15s}  {e.get('confidence',0):.0%}")
    buf = BytesIO()
    buf.write("\n".join(lines).encode("utf-8"))
    buf.seek(0)
    return buf
