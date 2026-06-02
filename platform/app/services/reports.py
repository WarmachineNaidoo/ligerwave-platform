from datetime import datetime, timezone, timedelta
from app.database import service
from io import BytesIO
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

def generate_report(home_id: str, months: int = 1) -> BytesIO:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30 * months)).isoformat()
    events = service.table("events").select("*").eq("home_id", home_id).gte("timestamp", cutoff).order("timestamp", desc=True).execute()
    data = events.data or []
    total = len(data)
    intrusions = sum(1 for e in data if e.get("event_type") == "intrusion")
    motions = sum(1 for e in data if e.get("event_type") == "motion")
    normals = sum(1 for e in data if e.get("event_type") in ("normal",))
    avg_conf = sum(e.get("confidence", 0) or 0 for e in data) / max(total, 1)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"CSI Security Report", styles["Title"]))
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph(f"Home: {home_id[:8]}...", styles["Normal"]))
    elements.append(Paragraph(f"Period: Last {months} month(s)", styles["Normal"]))
    elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    elements.append(Spacer(1, 8*mm))

    summary_data = [
        ["Metric", "Value"],
        ["Total Events", str(total)],
        ["Intrusions", str(intrusions)],
        ["Motion Events", str(motions)],
        ["Normal Events", str(normals)],
        ["Average Confidence", f"{avg_conf:.1%}"],
    ]
    t = Table(summary_data, colWidths=[120*mm, 60*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#0f172a")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 8*mm))

    if data:
        elements.append(Paragraph(f"Recent Events (last {min(total, 50)})", styles["Heading2"]))
        elements.append(Spacer(1, 3*mm))
        rows = [["Time", "Type", "Confidence", "Zone"]]
        for e in data[:50]:
            rows.append([
                e.get("timestamp", "")[:19],
                e.get("event_type", ""),
                f"{((e.get('confidence') or 0) * 100):.0f}%" if e.get("confidence") else "-",
                e.get("zone") or "-",
            ])
        t2 = Table(rows, colWidths=[80*mm, 40*mm, 30*mm, 30*mm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t2)

    doc.build(elements)
    buf.seek(0)
    return buf
