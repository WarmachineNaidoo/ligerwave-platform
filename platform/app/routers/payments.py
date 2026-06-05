from fastapi import APIRouter, HTTPException, Depends, Request
from app.middleware.auth import get_current_user
from app.config import settings
from app.services.log import logger
import json, hmac, hashlib

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/webhook")
async def payment_webhook(request: Request):
    body = await request.body()
    payload = json.loads(body)
    event_type = payload.get("event", "")
    data = payload.get("data", {})

    if event_type == "charge.success":
        txn_id = data.get("id")
        email = data.get("customer", {}).get("email")
        amount = data.get("amount")
        logger.info("payment_success", extra={"extra": {"txn_id": txn_id, "email": email, "amount": amount}})
        return {"status": "recorded"}

    if event_type in ("chargeback.create", "chargeback.remind"):
        txn_id = data.get("id")
        logger.critical("chargeback_received", extra={"extra": {"txn_id": txn_id, "event": event_type}})
        return {"status": "flagged", "action": "account_frozen"}

    return {"status": "received"}

@router.post("/create-checkout-session")
async def create_checkout_session(payload: dict = Depends(get_current_user)):
    user_id = payload.get("sub")
    return {
        "status": "demo_mode",
        "message": "Connect Stripe account to enable live payments. Test mode available.",
        "test_card": "4242 4242 4242 4242",
        "test_amount": "R30.00",
        "test_checkout_url": "/payments/test-checkout",
    }

@router.post("/dispute-package/{transaction_id}")
async def get_dispute_package(transaction_id: str, payload: dict = Depends(get_current_user)):
    return {
        "transaction_id": transaction_id,
        "status": "evidence_bundle_ready",
        "steps": [
            "Transaction record (ID, amount, IP, device fingerprint)",
            "Proof of service (CSI events during subscription)",
            "Consent audit trail (signed consent record)",
            "Login history (dashboard access during subscription)",
            "Email confirmation (delivery receipt)",
            "3DS authentication (bank verification)",
        ],
        "note": "Connect Paystack to enable automatic dispute submission via API.",
    }
