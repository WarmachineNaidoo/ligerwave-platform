import os
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from app.database import supabase, service
from app.models.schemas import UserCreate
from app.middleware.auth import get_current_user, require_role
from app.config import settings
from app.services.log import logger
import html

router = APIRouter(prefix="/auth", tags=["auth"])

_reset_pw_html = None

def _get_reset_page():
    global _reset_pw_html
    if _reset_pw_html is None:
        path = os.path.join(os.path.dirname(__file__), "..", "static", "reset-password.html")
        if os.path.isfile(path):
            html = open(path).read()
            html = html.replace("SUPABASE_URL_PLACEHOLDER", settings.supabase_url)
            html = html.replace("SUPABASE_KEY_PLACEHOLDER", settings.supabase_key)
            _reset_pw_html = html
    return _reset_pw_html

@router.get("/reset-password", include_in_schema=False)
async def serve_reset_page():
    html = _get_reset_page()
    if html:
        return HTMLResponse(html)
    return HTMLResponse("Page not found", status_code=404)

@router.post("/register")
async def register(body: UserCreate):
    try:
        result = supabase.auth.sign_up({
            "email": body.email,
            "password": body.password,
            "options": {"data": {"name": body.name}}
        })
        user = result.user
        if body.organization_id:
            service.table("users").insert({
                "id": user.id,
                "email": body.email,
                "name": body.name,
                "organization_id": str(body.organization_id)
            }).execute()
        return {"id": user.id, "email": user.email}
    except Exception as e:
        logger.error("registration_failed", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=400, detail="Registration failed. Please try again.")

class LoginRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

@router.post("/login")
async def login(body: LoginRequest):
    try:
        result = supabase.auth.sign_in_with_password({"email": body.email, "password": body.password})
        return {"access_token": result.session.access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error("login_failed", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=401, detail="Invalid email or password")

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=255)

@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    try:
        supabase.auth.reset_password_for_email(body.email, {
            "redirect_to": f"{settings.app_url}/auth/reset-password"
        })
        return {"message": "Password reset email sent"}
    except Exception as e:
        logger.error("forgot_password_failed", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=400, detail="Password reset request failed")

@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    redirect_to = f"{settings.app_url}/auth/callback"
    url = (f"{settings.supabase_url}/auth/v1/authorize"
           f"?provider={provider}"
           f"&redirect_to={redirect_to}")
    return {"url": url}

@router.get("/callback")
async def oauth_callback(error: str = Query(None)):
    if error:
        safe_error = html.escape(str(error))
        return HTMLResponse(f"<script>alert('OAuth error: {safe_error}');window.location.href='/';</script>")
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Signing in...</title>
    <script src="https://unpkg.com/@supabase/supabase-js@2"></script></head><body>
    <p>Completing sign in...</p>
    <script>
    (async function() {{
        var supabase = createClient('{settings.supabase_url}', '{settings.supabase_key}');
        var {{ data, error }} = await supabase.auth.exchangeCodeForSession(window.location.href);
        if (error) {{ alert('Auth error: ' + error.message); window.location.href = '/'; return; }}
        localStorage.setItem('token', data.session.access_token);
        window.location.href = '/';
    }})();
    </script></body></html>
    """)

@router.get("/me")
async def get_me(payload: dict = Depends(get_current_user)):
    return payload

@router.post("/mfa/enroll")
async def enroll_mfa(payload: dict = Depends(get_current_user)):
    session = supabase.auth.get_session()
    if not session:
        raise HTTPException(status_code=401, detail="No session")
    try:
        result = supabase.auth.mfa.enroll()
        return {"id": result.id, "type": result.type, "totp": result.totp}
    except Exception as e:
        logger.error("mfa_enroll_failed", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=400, detail="MFA enrollment failed")

class MfaVerifyRequest(BaseModel):
    factor_id: str
    code: str

@router.post("/mfa/verify")
async def verify_mfa(body: MfaVerifyRequest, payload: dict = Depends(get_current_user)):
    session = supabase.auth.get_session()
    if not session:
        raise HTTPException(status_code=401, detail="No session")
    try:
        challenge = supabase.auth.mfa.challenge({"factor_id": body.factor_id})
        verify = supabase.auth.mfa.verify({"factor_id": body.factor_id, "challenge_id": challenge.id, "code": body.code})
        return {"status": "verified", "verified": True}
    except Exception as e:
        logger.error("mfa_verify_failed", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=400, detail="MFA verification failed")

@router.post("/mfa/unenroll")
async def unenroll_mfa(factor_id: str = Query(...), payload: dict = Depends(get_current_user)):
    session = supabase.auth.get_session()
    if not session:
        raise HTTPException(status_code=401, detail="No session")
    try:
        supabase.auth.mfa.unenroll({"factor_id": factor_id})
        return {"status": "unenrolled"}
    except Exception as e:
        logger.error("mfa_unenroll_failed", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=400, detail="MFA unenrollment failed")

@router.get("/mfa/factors")
async def list_mfa_factors(payload: dict = Depends(get_current_user)):
    session = supabase.auth.get_session()
    if not session:
        raise HTTPException(status_code=401, detail="No session")
    try:
        result = supabase.auth.mfa.list_factors()
        return {"factors": result}
    except Exception as e:
        logger.error("mfa_list_factors_failed", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=400, detail="Failed to list MFA factors")
