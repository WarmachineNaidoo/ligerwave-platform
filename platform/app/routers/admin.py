from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.middleware.auth import get_current_user, require_role
from app.services.feature_flags import (
    get_all_features, get_feature, set_stage,
    add_tester, remove_tester, STAGES
)

router = APIRouter(prefix="/admin", tags=["admin"])


class StageRequest(BaseModel):
    feature_key: str = Field(..., min_length=1)
    stage: str = Field(..., min_length=2)

class TesterRequest(BaseModel):
    feature_key: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)


def _require_admin(payload: dict):
    role = payload.get("role") or payload.get("user_metadata", {}).get("role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="admin_only")


@router.get("/features")
async def list_feature_flags(payload: dict = Depends(get_current_user)):
    _require_admin(payload)
    return get_all_features()

@router.get("/features/{feature_key}")
async def get_feature_flag(feature_key: str, payload: dict = Depends(get_current_user)):
    _require_admin(payload)
    f = get_feature(feature_key)
    if not f:
        raise HTTPException(status_code=404, detail="feature_not_found")
    return {"key": feature_key, **f}

@router.post("/features/stage")
async def update_stage(body: StageRequest, payload: dict = Depends(get_current_user)):
    _require_admin(payload)
    return set_stage(body.feature_key, body.stage)

@router.post("/features/tester")
async def add_feature_tester(body: TesterRequest, payload: dict = Depends(get_current_user)):
    _require_admin(payload)
    return add_tester(body.feature_key, body.user_id)

@router.delete("/features/tester")
async def remove_feature_tester(feature_key: str, user_id: str, payload: dict = Depends(get_current_user)):
    _require_admin(payload)
    return remove_tester(feature_key, user_id)
