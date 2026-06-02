from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import settings

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(*roles: str):
    async def role_checker(payload: dict = Depends(get_current_user)) -> dict:
        user_role = payload.get("role", "consumer")
        if roles and user_role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return payload
    return role_checker
