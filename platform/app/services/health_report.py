import io
from datetime import datetime, timezone, timedelta
from app.database import service
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
import numpy as np

def generate_health_report(home_id: str, days: int = 30) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    dark_bg = HexColor("#0f172a")
    card_bg = HexColor("#1e293b")
    accent = HexColor("#22d3ee")
    text_color = HexColor("#e2e8f0")
    muted = HexColor("#64748b")

    story = []
    story.append(Paragraph("Ligerwave Health Report", styles["Title"]))
    story.append(Paragraph(f"Home: {home_id[:8]}... | Period: {days} days", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Sleep quality data
    events = service.table("events").select("*").eq("home_id", home_id).eq("event_type", "breathing").gte("timestamp", (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()).order("timestamp", desc=True).limit(500).execute()
    breath_events = events.data or []
    apneas = service.table("events").select("*").eq("home_id", home_id).eq("event_type", "apnea").gte("timestamp", (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()).execute()
    apnea_events = apneas.data or []

    if breath_events:
        avg_bpm = round(sum(e.get("confidence", 0) * 15 + 12 for e in breath_events) / len(breath_events), 1)
        story.append(Paragraph(f"<b>Sleep Summary</b>", styles["Heading2"]))
        story.append(Spacer(1, 6))
        data = [["Metric", "Value"],
                ["Avg Breathing Rate", f"{avg_bpm} BPM"],
                ["Nights Tracked", f"{days}"],
                ["Total Breathing Events", f"{len(breath_events)}"],
                ["Apnea/Hypopnea Events", f"{len(apnea_events)}"],
                ["AHI (Est.)", f"{round(len(apnea_events) / max(days, 1), 1)}"]]
        t = Table(data, colWidths=[3*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#22d3ee")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), card_bg),
            ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No sleep data available for this period.", styles["Normal"]))

    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>This report is for informational purposes only. Not a medical diagnosis.</i>", styles["Normal"]))
    story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))

    doc.build(story)
    buf.seek(0)
    return buf


def _group_by_night(events, bedtime_hour=20, wake_hour=8):
    """Group events by night (8pm-8am) and return {night_key: [events]}."""
    nights = {}
    for e in events:
        ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
        hour = ts.hour
        night_key = ts.strftime("%Y-%m-%d")
        if hour >= bedtime_hour:
            night_key = (ts + timedelta(days=1)).strftime("%Y-%m-%d")
        elif hour >= wake_hour:
            continue
        if night_key not in nights:
            nights[night_key] = []
        nights[night_key].append(e)
    return nights


def generate_weekly_wellness_report(home_id: str) -> io.BytesIO:
    now = datetime.now(timezone.utc)
    this_start = now - timedelta(days=7)
    prev_start = this_start - timedelta(days=7)

    all_events = service.table("events").select("event_type,confidence,timestamp,metadata").eq("home_id", home_id).gte("timestamp", prev_start.isoformat()).execute()
    rows = all_events.data or []

    current_events = [e for e in rows if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) >= this_start]
    prev_events = [e for e in rows if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) < this_start]

    cur_breath = [e for e in current_events if e.get("event_type") == "breathing"]
    cur_apnea = [e for e in current_events if e.get("event_type") == "apnea"]
    cur_falls = [e for e in current_events if e.get("event_type") == "fall"]

    prev_breath = [e for e in prev_events if e.get("event_type") == "breathing"]
    prev_apnea = [e for e in prev_events if e.get("event_type") == "apnea"]

    cur_avg_bpm = round(float(np.mean([e["confidence"] * 60 for e in cur_breath if e.get("confidence")])), 1) if cur_breath else 0
    prev_avg_bpm = round(float(np.mean([e["confidence"] * 60 for e in prev_breath if e.get("confidence")])), 1) if prev_breath else 0

    cur_ahi = round(len(cur_apnea) / 7.0, 1)
    prev_ahi = round(len(prev_apnea) / 7.0, 1)

    def trend(val, prev):
        if prev == 0:
            return "new"
        diff = val - prev
        if diff > 0.05 * abs(prev):
            return "declined"
        elif diff < -0.05 * abs(prev):
            return "improved"
        return "stable"

    breath_trend = trend(cur_avg_bpm, prev_avg_bpm) if prev_avg_bpm else "new"
    ahi_trend = trend(cur_ahi, prev_ahi) if prev_ahi else "new"

    cur_nights = _group_by_night(cur_breath)
    prev_nights = _group_by_night(prev_breath)

    def night_hours(night_events):
        if len(night_events) < 2:
            return 0
        timestamps = sorted(datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) for e in night_events)
        return round((timestamps[-1] - timestamps[0]).total_seconds() / 3600, 1)

    def apnea_per_night(night_key, apnea_list):
        return sum(1 for e in apnea_list if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).strftime("%Y-%m-%d") == night_key)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    card_bg = HexColor("#1e293b")
    text_color = HexColor("#e2e8f0")
    accent = HexColor("#22d3ee")
    muted = HexColor("#64748b")
    green = HexColor("#22c55e")
    red = HexColor("#ef4444")

    story = []
    story.append(Paragraph("Ligerwave Weekly Wellness Summary", styles["Title"]))
    story.append(Paragraph(f"Home: {home_id[:8]}...  |  Period: Last 7 days", styles["Normal"]))
    story.append(Paragraph(f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Breathing Rate</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))
    tdata = [["Metric", "This Week", "Last Week", "Trend"]]
    tdata.append(["Avg Breathing Rate", f"{cur_avg_bpm} BPM", f"{prev_avg_bpm} BPM" if prev_avg_bpm else "--", breath_trend])
    tdata.append(["AHI (Apnea-Hypopnea Index)", str(cur_ahi), str(prev_ahi) if prev_ahi else "--", ahi_trend])
    t = Table(tdata, colWidths=[100*mm, 40*mm, 40*mm, 40*mm])
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#22d3ee")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, -1), card_bg),
        ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#334155")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(tdata)):
        trend_val = tdata[i][3]
        if trend_val == "improved":
            style_cmds.append(('TEXTCOLOR', (3, i), (3, i), green))
        elif trend_val == "declined":
            style_cmds.append(('TEXTCOLOR', (3, i), (3, i), red))
    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Sleep Hours Tracked</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))
    sleep_rows = [["Night", "Sleep Hours", "Breathing Samples"]]
    for nk in sorted(cur_nights.keys(), reverse=True)[:7]:
        hrs = night_hours(cur_nights[nk])
        n_breath = len(cur_nights[nk])
        apnea_count = apnea_per_night(nk, cur_apnea)
        apnea_str = f" ({apnea_count} apnea)" if apnea_count else ""
        sleep_rows.append([nk, f"{hrs}h", f"{n_breath} samples{apnea_str}"])
    if len(sleep_rows) > 1:
        st = Table(sleep_rows, colWidths=[60*mm, 40*mm, 80*mm])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#22d3ee")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), card_bg),
            ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#334155")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(st)
    else:
        story.append(Paragraph("No sleep data available.", styles["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Apnea Events — AHI Trend by Night</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))
    ahi_rows = [["Night", "Apnea Events", "AHI", "Severity"]]
    for nk in sorted(cur_nights.keys(), reverse=True)[:7]:
        apnea_count = apnea_per_night(nk, cur_apnea)
        night_ahi = round(apnea_count / max(night_hours(cur_nights[nk]), 0.1), 1)
        severity = "severe" if night_ahi >= 30 else "moderate" if night_ahi >= 15 else "mild" if night_ahi >= 5 else "normal"
        ahi_rows.append([nk, str(apnea_count), str(night_ahi), severity])
    if len(ahi_rows) > 1:
        at = Table(ahi_rows, colWidths=[60*mm, 40*mm, 30*mm, 50*mm])
        at.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#22d3ee")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), card_bg),
            ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#334155")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(at)
    else:
        story.append(Paragraph("No apnea data available.", styles["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Fall Detection Events</b>", styles["Heading2"]))
    story.append(Spacer(1, 4))
    fall_rows = [["Date", "Confidence", "Status"]]
    for e in sorted(cur_falls, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]:
        ts = e.get("timestamp", "")[:10]
        conf = e.get("confidence", 0)
        status = "fall_detected" if conf > 0.6 else "possible_fall"
        fall_rows.append([ts, f"{conf:.0%}", status])
    if len(fall_rows) > 1:
        ft = Table(fall_rows, colWidths=[60*mm, 50*mm, 70*mm])
        ft.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#22d3ee")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), card_bg),
            ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#334155")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(ft)
    else:
        story.append(Paragraph("No fall events detected.", styles["Normal"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("<i>For informational purposes only. Not a medical diagnosis.</i>", styles["Normal"]))

    doc.build(story)
    buf.seek(0)
    return buf
