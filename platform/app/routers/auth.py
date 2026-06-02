from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.database import supabase
from app.models.schemas import UserCreate
from app.middleware.auth import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["auth"])

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
            supabase.table("users").insert({
                "id": user.id,
                "email": body.email,
                "name": body.name,
                "organization_id": str(body.organization_id)
            }).execute()
        return {"id": user.id, "email": user.email}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class LoginRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

@router.post("/login")
async def login(body: LoginRequest):
    try:
        result = supabase.auth.sign_in_with_password({"email": body.email, "password": body.password})
        return {"access_token": result.session.access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/me")
async def get_me(payload: dict = Depends(get_current_user)):
    return payload
