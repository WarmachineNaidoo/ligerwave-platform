from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from app.database import supabase, service
from app.middleware.auth import get_current_user
from app.middleware.ownership import verify_home_ownership
from app.services.audit import audit

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

class CreateSubscription(BaseModel):
    provider: str = Field(default="stripe", pattern="^(stripe|yoco)$")
    tier: str = Field(default="basic", pattern="^(basic|premium|wholesale)$")
    amount_cents: int = Field(default=3000, ge=0, le=100000)

@router.post("")
async def create_subscription(
    body: CreateSubscription,
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user)
):
    existing = service.table("subscriptions").select("*").eq("home_id", home_id).eq("status", "active").execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Active subscription already exists")
    sub = service.table("subscriptions").insert({
        "home_id": home_id,
        "provider": body.provider,
        "tier": body.tier,
        "amount_cents": body.amount_cents,
        "current_period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    }).execute()
    audit.log(payload.get("sub"), "subscription_created", "subscription", details={"tier": body.tier, "amount": body.amount_cents})
    return sub.data[0]

@router.get("")
async def get_subscription(home_id: str = Depends(verify_home_ownership)):
    result = service.table("subscriptions").select("*").eq("home_id", home_id).execute()
    return result.data

@router.post("/cancel")
async def cancel_subscription(
    home_id: str = Depends(verify_home_ownership),
    payload: dict = Depends(get_current_user)
):
    service.table("subscriptions").update({
        "status": "canceled",
        "canceled_at": datetime.now(timezone.utc).isoformat()
    }).eq("home_id", home_id).execute()
    audit.log(payload.get("sub"), "subscription_canceled", "subscription", resource_id=home_id)
    return {"status": "canceled"}
