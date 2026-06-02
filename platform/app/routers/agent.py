from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.database import service
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from datetime import datetime, timezone, timedelta
import json

router = APIRouter(prefix="/agent", tags=["agent"])

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)

INTENT_RULES = [
    (lambda q: any(w in q for w in ["how many", "count", "total", "number of"]), "count"),
    (lambda q: any(w in q for w in ["last", "recent", "latest", "newest"]), "recent"),
    (lambda q: any(w in q for w in ["intrusion", "alert", "breach", "intruder"]), "intrusions"),
    (lambda q: any(w in q for w in ["motion", "movement", "moving"]), "motion"),
    (lambda q: any(w in q for w in ["confidence", "confident", "sure"]), "confidence"),
    (lambda q: any(w in q for w in ["today", "daily", "24h", "24 hour"]), "today"),
    (lambda q: any(w in q for w in ["week", "weekly", "7 day"]), "week"),
    (lambda q: any(w in q for w in ["month", "monthly", "30 day"]), "month"),
    (lambda q: any(w in q for w in ["arm", "armed", "disarm", "disarmed"]), "arming"),
    (lambda q: any(w in q for w in ["zone", "room", "area", "location"]), "zone"),
    (lambda q: any(w in q for w in ["storage", "csi", "size", "data", "disk"]), "storage"),
]

def detect_intent(question: str) -> str:
    q = question.lower()
    for matcher, intent in INTENT_RULES:
        if matcher(q):
            return intent
    return "summary"

def answer_count(home_id: str, filter_type: Optional[str] = None, period: Optional[str] = None) -> dict:
    q = service.table("events").select("id", count="exact").eq("home_id", home_id)
    if filter_type:
        q = q.eq("event_type", filter_type)
    if period == "today":
        cutoff = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        q = q.gte("timestamp", cutoff)
    elif period == "week":
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        q = q.gte("timestamp", cutoff)
    elif period == "month":
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        q = q.gte("timestamp", cutoff)
    result = q.execute()
    return {"count": result.count if hasattr(result, 'count') else len(result.data), "period": period or "all"}

def answer_recent(home_id: str, limit: int = 10) -> dict:
    result = service.table("events").select("*").eq("home_id", home_id).order("timestamp", desc=True).limit(limit).execute()
    return {"events": result.data, "count": len(result.data)}

def answer_confidence(home_id: str) -> dict:
    result = service.table("events").select("confidence").eq("home_id", home_id).order("timestamp", desc=True).limit(100).execute()
    confs = [e.get("confidence", 0) or 0 for e in result.data]
    avg = sum(confs) / max(len(confs), 1)
    return {"average_confidence": round(avg, 4), "sample_size": len(confs), "high_confidence_count": sum(1 for c in confs if c >= 0.8)}

def answer_storage(home_id: str) -> dict:
    result = service.table("events").select("csi_size_bytes").eq("home_id", home_id).execute()
    total = sum(e.get("csi_size_bytes", 0) or 0 for e in result.data)
    mb = total / (1024 * 1024)
    return {"total_csi_storage_mb": round(mb, 2), "total_events": len(result.data)}

def answer_summary(home_id: str) -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    result = service.table("events").select("*").eq("home_id", home_id).gte("timestamp", cutoff).execute()
    data = result.data or []
    intrusions = sum(1 for e in data if e.get("event_type") == "intrusion")
    motions = sum(1 for e in data if e.get("event_type") == "motion")
    total = len(data)
    avg_conf = sum(e.get("confidence", 0) or 0 for e in data) / max(total, 1)
    return {
        "total_events_30d": total,
        "intrusions": intrusions,
        "motions": motions,
        "average_confidence": round(avg_conf, 4),
        "period": "30 days",
    }

@router.post("/query")
async def agent_query(
    body: QueryRequest,
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user),
):
    intent = detect_intent(body.question)
    q = body.question.lower()

    filter_type = None
    if intent in ("intrusions",):
        filter_type = "intrusion"
    elif intent in ("motion",):
        filter_type = "motion"

    period = None
    if intent == "today":
        period = "today"
    elif intent == "week":
        period = "week"
    elif intent == "month":
        period = "month"
    elif "today" in q or "24h" in q:
        period = "today"
    elif "week" in q:
        period = "week"
    elif "month" in q:
        period = "month"

    if intent == "count":
        data = answer_count(home_id, filter_type, period)
    elif intent == "recent":
        data = answer_recent(home_id)
    elif intent == "confidence":
        data = answer_confidence(home_id)
    elif intent == "storage":
        data = answer_storage(home_id)
    else:
        data = answer_summary(home_id)

    # Build natural language response
    lines = []
    if intent == "count" and "count" in data:
        label = filter_type or "events"
        lines.append(f"There are {data['count']} {label} in the {data['period']} period.")
    elif intent == "recent":
        lines.append(f"Found {data['count']} recent events.")
        if data["events"]:
            lines.append(f"Latest: {data['events'][0].get('event_type')} at {data['events'][0].get('timestamp')[:19]} (confidence {((data['events'][0].get('confidence') or 0)*100):.0f}%)")
    elif intent == "confidence":
        lines.append(f"Average confidence over last 100 events: {data['average_confidence']:.1%}")
        lines.append(f"High confidence events (80%+): {data['high_confidence_count']}")
    elif intent == "storage":
        lines.append(f"Total CSI storage used: {data['total_csi_storage_mb']} MB across {data['total_events']} events.")
    else:
        lines.append(f"Last 30 days: {data['total_events_30d']} total events.")
        lines.append(f"Intrusions: {data['intrusions']}, Motion events: {data['motions']}")
        lines.append(f"Average confidence: {data['average_confidence']:.1%}")

    return {
        "question": body.question,
        "intent": intent,
        "answer": " ".join(lines),
        "data": data,
    }

@router.get("/health")
async def agent_health():
    return {"status": "ok", "model": "rule-based", "intents": [r[1] for r in INTENT_RULES]}
