from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from httpx import AsyncClient
from app.config import settings

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    url = f"{settings.supabase_url}/auth/v1/user"
    async with AsyncClient() as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}", "apikey": settings.supabase_key})
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = resp.json()
        return {"sub": user["id"], "email": user.get("email"), "role": "consumer"}

def require_role(*roles: str):
    async def role_checker(payload: dict = Depends(get_current_user)) -> dict:
        user_role = payload.get("role", "consumer")
        if roles and user_role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return payload
    return role_checker