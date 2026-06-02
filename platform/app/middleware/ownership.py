from fastapi import Depends, HTTPException
from app.database import supabase
from app.middleware.auth import get_current_user

async def verify_home_ownership(
    home_id: str,
    payload: dict = Depends(get_current_user)
) -> str:
    user_id = payload.get("sub")
    result = supabase.table("users").select("organization_id").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=403, detail="User not found")
    org_id = result.data[0].get("organization_id")
    home = supabase.table("homes").select("id,organization_id").eq("id", home_id).execute()
    if not home.data:
        raise HTTPException(status_code=404, detail="Home not found")
    if home.data[0].get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return home_id
